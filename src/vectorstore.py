"""Vector store initialization and management functions."""
import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from src.config import (
    GOOGLE_API_KEY, 
    PINECONE_API_KEY, 
    PINECONE_INDEX_NAME, 
    PINECONE_NAMESPACE
)

def initialize_vectorstore(status_callback=None):
    """Initialize connection to existing Pinecone index and vectorstore.
    
    Args:
        status_callback: Optional function to call with status updates
        
    Returns:
        PineconeVectorStore or None if initialization fails
    """
    def update_status(msg):
        if status_callback:
            status_callback(msg)
        else:
            print(msg)
    
    # Set environment variables for libraries that require them
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
    
    # Initialize embeddings
    update_status("Initializing Google AI embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # Initialize Pinecone
    update_status("Connecting to Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index exists
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        update_status(f"Error: Pinecone index '{PINECONE_INDEX_NAME}' not found!")
        return None
    
    # Check if vectors exist in Pinecone
    index = pc.Index(PINECONE_INDEX_NAME)
    stats = index.describe_index_stats()
    vector_count = stats.get('namespaces', {}).get(PINECONE_NAMESPACE, {}).get('vector_count', 0)
    
    if vector_count == 0:
        update_status(f"Error: No vectors found in namespace '{PINECONE_NAMESPACE}'!")
        return None
    
    update_status(f"Found {vector_count} vectors in Pinecone. Connecting to vector store...")
    
    # Initialize vectorstore connection
    vectorstore = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings,
        namespace=PINECONE_NAMESPACE
    )
    
    update_status("Successfully connected to Pinecone vector store!")
    return vectorstore