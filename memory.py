from langchain.memory import ConversationBufferMemory
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


# Individual Chat Memory
def create_agent_memory():
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )


#  Shared Vector Memory (REAL)
def create_shared_memory():

   
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # Create empty vector store
    vector_store = FAISS.from_texts(
        ["initial memory"],
        embedding=embeddings
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3}
    )

    memory = VectorStoreRetrieverMemory(
        retriever=retriever
    )

    return memory