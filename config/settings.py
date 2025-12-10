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
    
    # Model settings
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
    
    # API Keys (loaded from secrets or env)
    GOOGLE_API_KEY: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    
    @classmethod
    def load_from_secrets(cls) -> 'AppConfig':
        """Load configuration from Streamlit secrets or environment"""
        config = cls()
        
        # Try Streamlit secrets first
        try:
            config.GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
            config.QDRANT_URL = st.secrets.get("QDRANT_URL", "")
            config.QDRANT_API_KEY = st.secrets.get("QDRANT_API_KEY", "")
        except:
            # Fallback to environment variables
            config.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
            config.QDRANT_URL = os.getenv("QDRANT_URL", "")
            config.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        
        return config
    
    def is_valid(self) -> bool:
        """Check if all required keys are present"""
        return bool(
            self.GOOGLE_API_KEY and 
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