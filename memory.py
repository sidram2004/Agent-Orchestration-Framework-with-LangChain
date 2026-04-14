from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


def create_agent_memory():
    """Per-agent short-term conversational memory."""
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)


def create_shared_memory():
    """Shared vector memory — persists context across all agents."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(["initial memory"], embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    return VectorStoreRetrieverMemory(retriever=retriever)