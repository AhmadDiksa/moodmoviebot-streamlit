"""
Qdrant Database Manager
File: core/qdrant_manager.py
"""

import streamlit as st
from typing import List, Optional, Dict, Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class QdrantManager:
    """Manage Qdrant database operations"""
    
    def __init__(self, config: AppConfig):
        """
        Initialize Qdrant Manager
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._client = None
    
    @property
    def client(self) -> QdrantClient:
        """Lazy load Qdrant client"""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    def _initialize_client(self) -> QdrantClient:
        """Initialize Qdrant client"""
        logger.debug(f"Initializing Qdrant client - URL: {self.config.QDRANT_URL}")
        logger.debug(f"Collection name: {self.config.COLLECTION_NAME}")
        try:
            client = QdrantClient(
                url=self.config.QDRANT_URL,
                api_key=self.config.QDRANT_API_KEY
            )
            
            # Test connection
            logger.debug("Testing Qdrant connection...")
            collections = client.get_collections()
            logger.debug(f"Available collections: {[c.name for c in collections.collections]}")
            
            logger.info("Qdrant client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def search_by_genres(
        self, 
        genre_ids: List[int], 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search movies by genre IDs
        
        Args:
            genre_ids: List of genre IDs to search
            limit: Maximum number of results
        
        Returns:
            List of movie payloads
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Searching movies by genres - IDs: {genre_ids}, Limit: {limit}")
        
        try:
            if not genre_ids:
                logger.warning("No genre IDs provided for search")
                return []
            
            # Build filter
            logger.debug("Building Qdrant filter...")
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="genre_ids",
                        match=MatchAny(any=genre_ids)
                    )
                ]
            )
            
            # Execute search
            logger.debug(f"Executing scroll query on collection: {self.config.COLLECTION_NAME}")
            points, _ = self.client.scroll(
                collection_name=self.config.COLLECTION_NAME,
                scroll_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            logger.debug(f"Query returned {len(points)} points")
            
            # Extract payloads
            results = [point.payload for point in points]
            
            duration = time.time() - start_time
            logger.info(f"Found {len(results)} movies for genres {genre_ids} in {duration:.2f}s")
            
            if results:
                logger.debug(f"Sample movie titles: {[r.get('title', 'Unknown')[:30] for r in results[:3]]}")
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Search by genres failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.debug(f"Genre IDs that failed: {genre_ids}")
            return []
    
    def get_movie_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Get movie by exact title
        
        Args:
            title: Movie title
        
        Returns:
            Movie payload or None if not found
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Searching for movie by title: {title}")
        
        try:
            points, _ = self.client.scroll(
                collection_name=self.config.COLLECTION_NAME,
                limit=100,  # Get more to find exact match
                with_payload=True,
                with_vectors=False
            )
            
            logger.debug(f"Scrolled {len(points)} points for title search")
            
            # Find exact match (case-insensitive)
            title_lower = title.lower()
            for point in points:
                if point.payload.get('title', '').lower() == title_lower:
                    duration = time.time() - start_time
                    logger.info(f"Found movie '{title}' in {duration:.2f}s")
                    return point.payload
            
            duration = time.time() - start_time
            logger.warning(f"Movie not found: {title} (searched {len(points)} movies in {duration:.2f}s)")
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Get movie by title failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test Qdrant connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.get_collections()
            logger.info("Qdrant connection test: SUCCESS")
            return True
        except Exception as e:
            logger.error(f"Qdrant connection test: FAILED - {e}")
            return False

@st.cache_resource
def get_qdrant_manager(config: AppConfig) -> QdrantManager:
    """
    Get cached Qdrant Manager instance
    
    Args:
        config: Application configuration
    
    Returns:
        QdrantManager instance
    """
    return QdrantManager(config)