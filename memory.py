from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


def create_agent_memory():
    """Per-agent short-term conversational memory."""
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)


def get_embeddings():
    """Utility to get the standard embedding model."""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def create_shared_memory():
    """Shared vector memory — persists context across all agents."""
    embeddings = get_embeddings()
    vector_store = FAISS.from_texts(["initial memory"], embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    return VectorStoreRetrieverMemory(retriever=retriever)


import os

def create_doc_retriever(text, chat_id=None):
    """
    Advanced RAG: Splits document text and creates/updates a local FAISS index.
    Matches your diagram: PL -> Text Splitter -> Embeddings -> Local FAISS Database
    """
    if not text or len(text.strip()) < 10:
        return load_doc_retriever(chat_id)
        
    # 1. Split text into chunks (matching the diagram)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    chunks = text_splitter.split_text(text)
    embeddings = get_embeddings()
    
    # 2. Local FAISS Database Node
    db_path = f"chat_docs/vector_db_{chat_id}" if chat_id else None
    
    if db_path and os.path.exists(db_path):
        # Update existing database
        vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        vector_store.add_texts(chunks)
    else:
        # Create new database
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    
    # 3. Persist to disk (Making it a real Database)
    if db_path:
        os.makedirs("chat_docs", exist_ok=True)
        vector_store.save_local(db_path)
        
    return vector_store.as_retriever(search_kwargs={"k": 4})

def load_doc_retriever(chat_id):
    """Loads an existing FAISS index from disk if it exists."""
    if not chat_id:
        return None
        
    db_path = f"chat_docs/vector_db_{chat_id}"
    if os.path.exists(db_path):
        try:
            embeddings = get_embeddings()
            vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
            return vector_store.as_retriever(search_kwargs={"k": 4})
        except Exception:
            return None
    return None