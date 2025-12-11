"""
Configuration and Constants
File: config/settings.py
"""

from dataclasses import dataclass
from typing import Optional
import streamlit as st
import os

@dataclass
class AppConfig:
    """Application configuration"""
    
    # LLM Provider settings
    LLM_PROVIDER: str = "gemini"  # Options: gemini, groq, openai
    MODEL_NAME: str = "gemini-flash-latest"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2000
    
    # Cache settings
    CACHE_TTL: int = 3600  # 1 hour
    MAX_CACHE_ENTRIES: int = 100
    
    # UI settings
    MAX_CHAT_HISTORY: int = 50
    MOVIES_PER_REQUEST: int = 5
    
    # Database settings
    COLLECTION_NAME: str = "moodviedb"
    
    # Embedding & Semantic Search settings
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    USE_SEMANTIC_SEARCH: bool = True
    
    # API Keys (loaded from secrets or env)
    # Gemini
    GOOGLE_API_KEY: str = ""
    # Groq
    GROQ_API_KEY: str = ""
    # OpenAI
    OPENAI_API_KEY: str = ""
    # Qdrant
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    
    @classmethod
    def load_from_secrets(cls) -> 'AppConfig':
        """Load configuration from Streamlit secrets or environment"""
        config = cls()
        
        # Try Streamlit secrets first
        try:
            # LLM Provider
            config.LLM_PROVIDER = st.secrets.get("LLM_PROVIDER", "gemini").lower()
            config.MODEL_NAME = st.secrets.get("MODEL_NAME", config.MODEL_NAME)
            config.TEMPERATURE = float(st.secrets.get("TEMPERATURE", config.TEMPERATURE))
            config.MAX_TOKENS = int(st.secrets.get("MAX_TOKENS", config.MAX_TOKENS))
            
            # API Keys
            config.GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
            config.GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
            config.OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
            config.QDRANT_URL = st.secrets.get("QDRANT_URL", "")
            config.QDRANT_API_KEY = st.secrets.get("QDRANT_API_KEY", "")
        except:
            # Fallback to environment variables
            config.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
            config.MODEL_NAME = os.getenv("MODEL_NAME", config.MODEL_NAME)
            config.TEMPERATURE = float(os.getenv("TEMPERATURE", config.TEMPERATURE))
            config.MAX_TOKENS = int(os.getenv("MAX_TOKENS", config.MAX_TOKENS))
            
            config.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
            config.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
            config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
            config.QDRANT_URL = os.getenv("QDRANT_URL", "")
            config.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        
        return config
    
    def get_llm_api_key(self) -> str:
        """Get API key for current LLM provider"""
        provider = self.LLM_PROVIDER.lower()
        if provider == "gemini":
            return self.GOOGLE_API_KEY
        elif provider == "groq":
            return self.GROQ_API_KEY
        elif provider == "openai":
            return self.OPENAI_API_KEY
        else:
            return ""
    
    def is_valid(self) -> bool:
        """Check if all required keys are present"""
        llm_key = self.get_llm_api_key()
        return bool(
            llm_key and 
            self.QDRANT_URL and 
            self.QDRANT_API_KEY
        )

# Color scheme - Netflix Red Theme
class Colors:
    """App color scheme - Netflix Red"""
    PRIMARY = "#E50914"  # Netflix Red
    SECONDARY = "#B20710"  # Darker Netflix Red
    BACKGROUND = "#0e1117"
    CARD_BG = "rgba(255, 255, 255, 0.1)"
    TEXT = "#ffffff"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#E50914"  # Use Netflix red for errors too

# Mood options
MOOD_OPTIONS = [
    "senang", "sedih", "marah", "cemas", "lelah", 
    "sakit", "excited", "bosan", "netral", "frustrasi",
    "hopeful", "nostalgic", "romantic", "adventurous"
]

# Genre options for recommendations
GENRE_OPTIONS = [
    "Comedy", "Animation", "Family", "Romance", 
    "Adventure", "Drama", "Action", "Thriller",
    "Fantasy", "Science Fiction", "Horror", "Mystery"
]

# Emotion type mapping
EMOTION_TYPES = {
    "positive": ["senang", "excited", "hopeful", "romantic", "adventurous"],
    "neutral": ["netral", "bosan"],
    "negative": ["sedih", "marah", "cemas", "lelah", "sakit", "frustrasi"]
}