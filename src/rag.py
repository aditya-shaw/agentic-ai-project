import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_FILE = BASE_DIR / "data" / "return_policy.txt"

# In-memory cache for vectorstore session
_vectorstore_cache = {}


def get_policy_text() -> str:
    """Reads the raw return policy text."""
    if POLICY_FILE.exists():
        with open(POLICY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "No return policy found."


def get_or_create_vectorstore(api_key: str):
    """Initializes or retrieves cached ChromaDB vector store using Gemini embeddings."""
    global _vectorstore_cache
    if "store" in _vectorstore_cache and _vectorstore_cache.get("key") == api_key:
        return _vectorstore_cache["store"]

    text = get_policy_text()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=60,
        separators=["\n\n", "\n", " ", ""]
    )
    docs = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": "data/return_policy.txt"}]
    )

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="company_return_policy"
    )

    _vectorstore_cache["store"] = vectorstore
    _vectorstore_cache["key"] = api_key
    return vectorstore


def query_policy(query: str, api_key: str, k: int = 3) -> str:
    """
    RAG Retrieval:
    Uses vector similarity search over ChromaDB embeddings.
    Includes a graceful fallback to text filtering if embeddings are loading.
    """
    try:
        if api_key and api_key.strip():
            store = get_or_create_vectorstore(api_key.strip())
            results = store.similarity_search(query, k=k)
            if results:
                return "\n\n---\n\n".join([doc.page_content for doc in results])
    except Exception:
        # Fallback to direct policy matching if vector service encounters network error
        pass

    # Direct chunk search fallback
    raw_text = get_policy_text()
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    keywords = [w.lower() for w in query.split() if len(w) > 3]

    scored = []
    for p in paragraphs:
        score = sum(1 for kw in keywords if kw in p.lower())
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return "\n\n---\n\n".join([p for _, p in scored[:k]])
    return raw_text[:800]
