from langchain_community.embeddings import HuggingFaceEmbeddings
import os

def download():
    print("--- Pre-downloading AI Models for Render ---")
    model_name = "all-MiniLM-L6-v2"
    # This triggers the download and saves it to the default cache directory
    HuggingFaceEmbeddings(model_name=model_name)
    print(f"--- Model {model_name} downloaded successfully! ---")

if __name__ == "__main__":
    download()
