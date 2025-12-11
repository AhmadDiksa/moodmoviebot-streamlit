"""
Embedding Manager for Sentence Transformers
File: core/embedding_manager.py

Manages sentence transformer model for encoding text to vectors
"""

import streamlit as st
import logging
from typing import List, Optional
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """
    Manage sentence transformer model for text embeddings
    
    Uses lazy loading and caching to avoid reloading model on each request
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize Embedding Manager
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self._model = None
        logger.info(f"EmbeddingManager initialized with model: {model_name}")
    
    @property
    def model(self):
        """Lazy load sentence transformer model"""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer(self.model_name)
            logger.info(f"Model {self.model_name} loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def encode_query(self, text: str) -> Optional[List[float]]:
        """
        Encode query text to vector
        
        Args:
            text: Query text to encode
        
        Returns:
            List of floats representing the embedding vector, or None if encoding fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for encoding")
            return None
        
        try:
            logger.debug(f"Encoding query text (length: {len(text)} chars)")
            vector = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            vector_list = vector.tolist()
            logger.debug(f"Encoded to vector of dimension {len(vector_list)}")
            return vector_list
        except Exception as e:
            logger.error(f"Failed to encode query text: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def encode_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Encode multiple texts to vectors (batch processing)
        
        Args:
            texts: List of texts to encode
        
        Returns:
            List of embedding vectors, or None if encoding fails
        """
        if not texts:
            logger.warning("Empty texts list provided for batch encoding")
            return None
        
        try:
            logger.debug(f"Batch encoding {len(texts)} texts")
            vectors = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            vectors_list = [v.tolist() for v in vectors]
            logger.debug(f"Batch encoded to {len(vectors_list)} vectors of dimension {len(vectors_list[0]) if vectors_list else 0}")
            return vectors_list
        except Exception as e:
            logger.error(f"Failed to batch encode texts: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return None

@st.cache_resource
def get_embedding_manager(_config: AppConfig = None, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> EmbeddingManager:
    """
    Get cached Embedding Manager instance
    
    Args:
        _config: Application configuration (unused, for cache key)
        model_name: Name of the sentence transformer model
    
    Returns:
        EmbeddingManager instance
    """
    return EmbeddingManager(model_name=model_name)

