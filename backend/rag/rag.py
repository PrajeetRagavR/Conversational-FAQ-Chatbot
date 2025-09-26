from langchain_community.document_loaders import PyPDFLoader, TextLoader
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def load_documents(file_path: str):
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == ".pdf":
        loader = PyPDFLoader(file_path)
    elif file_extension.lower() == ".txt":
        loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    documents = loader.load()
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    splits = text_splitter.split_documents(documents)
    return splits

def create_vector_store(splits, collection_name: str):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Always create or get the collection and add documents
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        client=client,
        collection_name=collection_name,
        collection_metadata={"hnsw:space": "cosine"}, # Explicitly setting HNSW space
    )
    
    print(f"Documents added to Chroma collection: {collection_name}")
    
    return vectorstore

def process_document_for_rag(file_path: str, collection_name: str):
    documents = load_documents(file_path)
    splits = split_documents(documents)
    vectorstore = create_vector_store(splits, collection_name)
    print(f"Processed document {file_path} and added to vector store.")
    return vectorstore.as_retriever()


def get_retriever(vectorstore, k: int = 10):
    return vectorstore.as_retriever(search_kwargs={"k": k})