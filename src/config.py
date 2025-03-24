"""Configuration module for loading environment variables and app settings."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Vector Database Configuration
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "connecticut-legal-assistant")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "legal-sections")

# Model Parameters
EMBEDDING_DIMENSION = 768  # Google's embedding-001 dimension
GROQ_MODEL = "deepseek-r1-distill-llama-70b"
TEMPERATURE = 0.3
MAX_TOKENS = 2048
TOP_P = 0.9

# Application Settings
MAX_RESULTS = 5
MAX_HISTORY = 6  # Maximum number of conversation exchanges to include

DEFAULT_JUDGE_PERSONALITY = "neutral"
DEFAULT_OPPOSING_COUNSEL_STRATEGY = "standard"