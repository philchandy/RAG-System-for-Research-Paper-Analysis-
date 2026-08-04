from ingestion import extract_text_from_pdf
from chunking import chunk_text

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from pathlib import Path
import shutil

from config import CHROMA_DIR, EMBEDDING_MODEL

def build_vector_store_from_pdf(pdf_path):
    """
    Extracts text from a PDF, chunks it, and builds a vector store using Chroma.
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Create Document objects
    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "chunk_id": f"chunk_{index:04d}",
                "section": chunk["section"],
            },
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Create Chroma vector store
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    CHROMA_DIR.mkdir(exist_ok=True)

    vector_store = Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=CHROMA_DIR
    )
    
    print(f"Vector store built and saved to {vector_store}")