from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

# Use absolute path so it works regardless of where Python is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_DOCS_DIR = os.path.join(BASE_DIR, "chat_docs")


def create_agent_memory():
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# Global embeddings singleton to avoid re-loading the model
_EMBEDDINGS = None

def get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        print("[Memory] Loading embeddings model (MiniLM)...")
        _EMBEDDINGS = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _EMBEDDINGS


def create_shared_memory():
    embeddings = get_embeddings()
    vector_store = FAISS.from_texts(["initial memory"], embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    return VectorStoreRetrieverMemory(retriever=retriever)


def _safe_id(chat_id):
    """Make chat_id safe for use as a folder name."""
    return str(chat_id).replace(" ", "_").replace("/", "_").replace("\\", "_")


def _all_db_paths(chat_id):
    """
    Return all possible DB paths to check — new safe path first, then old path with spaces.
    This ensures backward compatibility with databases saved before this fix.
    """
    if not chat_id:
        return []
    chat_id = str(chat_id)
    paths = []
    # New safe path (underscores)
    safe = _safe_id(chat_id)
    paths.append(os.path.join(CHAT_DOCS_DIR, f"vector_db_{safe}"))
    # Old path with spaces (backward compatibility)
    if safe != chat_id:
        paths.append(os.path.join(CHAT_DOCS_DIR, f"vector_db_{chat_id}"))
    return paths


def _primary_db_path(chat_id):
    """The canonical path where new databases are saved (always uses safe underscores)."""
    if not chat_id:
        return None
    return os.path.join(CHAT_DOCS_DIR, f"vector_db_{_safe_id(chat_id)}")


def create_doc_retriever(text, chat_id=None, overwrite=False):
    """
    Create or update a FAISS vector store from document text.
    If text is empty, loads the existing DB instead.
    If overwrite is True, starts fresh even if a DB exists.
    """
    if not text or len(text.strip()) < 10:
        return load_doc_retriever(chat_id)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    embeddings = get_embeddings()

    db_path = _primary_db_path(chat_id)

    # Check if any existing DB exists (old or new path format)
    existing_path = None
    if not overwrite:
        for p in _all_db_paths(chat_id):
            if os.path.exists(p):
                existing_path = p
                break

    if existing_path:
        try:
            vector_store = FAISS.load_local(existing_path, embeddings, allow_dangerous_deserialization=True)
            vector_store.add_texts(chunks)
        except Exception as e:
            print(f"[create_doc_retriever] Error loading for append: {e}")
            vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    else:
        # If overwriting, remove the old folder first
        if overwrite and db_path and os.path.exists(db_path):
            import shutil
            try:
                shutil.rmtree(db_path, ignore_errors=True)
                print(f"[create_doc_retriever] Overwriting: removed old DB at {db_path}")
            except Exception as e:
                print(f"[create_doc_retriever] Error removing old DB: {e}")
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)

    if db_path:
        os.makedirs(CHAT_DOCS_DIR, exist_ok=True)
        vector_store.save_local(db_path)
        print(f"[create_doc_retriever] Saved DB to: {db_path}")

    return vector_store.as_retriever(search_kwargs={"k": 8})


def load_doc_retriever(chat_id):
    """
    Load an existing FAISS DB from disk.
    Tries all path formats (new safe path + old path with spaces).
    """
    if not chat_id:
        return None

    for db_path in _all_db_paths(chat_id):
        print(f"[load_doc_retriever] Checking: {db_path} | exists: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            try:
                embeddings = get_embeddings()
                vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
                print(f"[load_doc_retriever] Loaded from: {db_path}")
                return vector_store.as_retriever(search_kwargs={"k": 8})
            except Exception as e:
                print(f"[load_doc_retriever] ERROR at {db_path}: {e}")
                continue

    print(f"[load_doc_retriever] No DB found for chat_id='{chat_id}'")
    return None


def has_vector_db(chat_id):
    """Returns True if a FAISS DB exists for this chat_id (checks all path formats)."""
    if not chat_id:
        return False
    return any(os.path.exists(p) for p in _all_db_paths(chat_id))

# Eager load embeddings at startup to prevent request timeouts
try:
    get_embeddings()
except Exception as e:
    print(f"[Memory] Warning: Eager embeddings load failed: {e}")


def rename_vector_db(old_chat_id, new_chat_id):
    """
    Rename the FAISS vector DB folder when a workspace is renamed.
    Tries all known path formats for the old chat_id and moves to the new canonical path.
    Returns True if renamed successfully, False if nothing was found or an error occurred.
    """
    if not old_chat_id or not new_chat_id or old_chat_id == new_chat_id:
        return False

    new_path = _primary_db_path(new_chat_id)
    if not new_path:
        return False

    for old_path in _all_db_paths(old_chat_id):
        if os.path.exists(old_path):
            try:
                import shutil
                os.makedirs(CHAT_DOCS_DIR, exist_ok=True)
                shutil.move(old_path, new_path)
                print(f"[rename_vector_db] Moved '{old_path}' -> '{new_path}'")
                return True
            except Exception as e:
                print(f"[rename_vector_db] ERROR moving '{old_path}' -> '{new_path}': {e}")
                return False

    print(f"[rename_vector_db] No DB found for old_chat_id='{old_chat_id}'")
    return False