"""
Qdrant Database Manager
File: core/qdrant_manager.py
"""

import streamlit as st
from typing import List, Optional, Dict, Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue, SearchRequest
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class QdrantManager:
    """
    Manage Qdrant database operations
    
    IMPORTANT: This class ONLY interacts with Qdrant database.
    No fallback to external APIs (TMDB, OMDB, etc.) is implemented.
    All movie data must come from Qdrant.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize Qdrant Manager
        
        Args:
            config: Application configuration
        
        Raises:
            ValueError: If Qdrant URL or API key is missing
        """
        if not config.QDRANT_URL:
            raise ValueError("QDRANT_URL is required. Movie search ONLY uses Qdrant database.")
        if not config.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is required. Movie search ONLY uses Qdrant database.")
        
        self.config = config
        self._client = None
        logger.info("QdrantManager initialized - ONLY using Qdrant database for movie data")
    
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
        Search movies by genre IDs from Qdrant ONLY
        
        IMPORTANT: This method ONLY searches Qdrant database. No external APIs are used.
        If Qdrant fails, returns empty list. No fallback to other sources.
        
        Args:
            genre_ids: List of genre IDs to search
            limit: Maximum number of results
        
        Returns:
            List of movie payloads from Qdrant (empty list if search fails)
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Searching movies by genres in Qdrant ONLY - IDs: {genre_ids}, Limit: {limit}")
        logger.debug("IMPORTANT: Movie search uses ONLY Qdrant database. No external APIs.")
        
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
            logger.info(f"Found {len(results)} movies from Qdrant for genres {genre_ids} in {duration:.2f}s")
            
            if results:
                logger.debug(f"Sample movie titles from Qdrant: {[r.get('title', 'Unknown')[:30] for r in results[:3]]}")
            elif len(results) == 0:
                logger.warning(f"No movies found in Qdrant for genres {genre_ids}. Returning empty list (no fallback to other sources).")
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Qdrant search by genres failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning empty list.")
            logger.debug(f"Genre IDs that failed: {genre_ids}")
            # Return empty list - NO fallback to other sources
            return []
    
    def get_movie_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Get movie by exact title from Qdrant ONLY
        
        IMPORTANT: This method ONLY searches Qdrant database. No external APIs are used.
        If movie not found in Qdrant, returns None. No fallback to other sources.
        
        Args:
            title: Movie title
        
        Returns:
            Movie payload from Qdrant or None if not found (no fallback to other sources)
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Searching for movie by title in Qdrant ONLY: {title}")
        logger.debug("IMPORTANT: Movie search uses ONLY Qdrant database. No external APIs.")
        
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
            logger.warning(f"Movie '{title}' not found in Qdrant database (searched {len(points)} movies in {duration:.2f}s)")
            logger.debug("IMPORTANT: No fallback to external APIs. Returning None.")
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Qdrant get movie by title failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning None.")
            # Return None - NO fallback to other sources
            return None
    
    def get_movie_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Get movie by TMDB ID from Qdrant ONLY
        
        IMPORTANT: This method ONLY searches Qdrant database. No external APIs are used.
        If movie not found in Qdrant, returns None. No fallback to other sources.
        
        Args:
            tmdb_id: TMDB ID of the movie
        
        Returns:
            Movie payload from Qdrant or None if not found (no fallback to other sources)
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Searching for movie by TMDB ID in Qdrant ONLY: {tmdb_id}")
        logger.debug("IMPORTANT: Movie search uses ONLY Qdrant database. No external APIs.")
        
        try:
            # Build filter for exact tmdb_id match
            logger.debug("Building Qdrant filter for tmdb_id...")
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="tmdb_id",
                        match=MatchValue(value=tmdb_id)
                    )
                ]
            )
            
            # Execute search
            logger.debug(f"Executing scroll query with tmdb_id filter on collection: {self.config.COLLECTION_NAME}")
            points, _ = self.client.scroll(
                collection_name=self.config.COLLECTION_NAME,
                scroll_filter=qdrant_filter,
                limit=1,  # Only need one result
                with_payload=True,
                with_vectors=False
            )
            
            logger.debug(f"Query returned {len(points)} points for tmdb_id {tmdb_id}")
            
            if points and len(points) > 0:
                duration = time.time() - start_time
                movie = points[0].payload
                logger.info(f"Found movie with tmdb_id {tmdb_id} ('{movie.get('title', 'Unknown')}') in {duration:.2f}s")
                return movie
            
            duration = time.time() - start_time
            logger.warning(f"Movie with tmdb_id {tmdb_id} not found in Qdrant database (searched in {duration:.2f}s)")
            logger.debug("IMPORTANT: No fallback to external APIs. Returning None.")
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Qdrant get movie by tmdb_id failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning None.")
            # Return None - NO fallback to other sources
            return None
    
    def search_by_semantic(
        self,
        query_vector: List[float],
        genre_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search movies by semantic similarity using vector embeddings from Qdrant ONLY
        
        IMPORTANT: This method ONLY searches Qdrant database using vector similarity.
        No external APIs are used. If Qdrant fails, returns empty list. No fallback to other sources.
        
        Args:
            query_vector: Query vector (embedding) for semantic search
            genre_ids: Optional list of genre IDs to filter results
            limit: Maximum number of results
        
        Returns:
            List of movie dictionaries with similarity scores (empty list if search fails)
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Semantic search in Qdrant ONLY - Vector dim: {len(query_vector)}, Limit: {limit}")
        if genre_ids:
            logger.debug(f"With genre filter: {genre_ids}")
        logger.debug("IMPORTANT: Semantic search uses ONLY Qdrant database. No external APIs.")
        
        try:
            if not query_vector:
                logger.warning("Empty query vector provided for semantic search")
                return []
            
            # Build filter for genre_ids if provided
            qdrant_filter = None
            if genre_ids:
                logger.debug("Building genre filter for semantic search...")
                qdrant_filter = Filter(
                    must=[
                        FieldCondition(
                            key="genre_ids",
                            match=MatchAny(any=genre_ids)
                        )
                    ]
                )
            
            # Execute semantic search using client.query_points()
            logger.debug(f"Executing semantic search on collection: {self.config.COLLECTION_NAME}")
            query_response = self.client.query_points(
                collection_name=self.config.COLLECTION_NAME,
                query=query_vector,  # query can be a vector (list[float])
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            logger.debug(f"Semantic search returned {len(query_response.points)} results")
            
            # Extract payloads and similarity scores
            results = []
            for point in query_response.points:
                movie_data = point.payload.copy() if point.payload else {}
                # Add similarity score to movie data
                movie_data['similarity_score'] = point.score
                results.append(movie_data)
            
            duration = time.time() - start_time
            logger.info(f"Found {len(results)} movies from semantic search in {duration:.2f}s")
            
            if results:
                top_similarities = [f"{r.get('title', 'Unknown')[:30]}: {r.get('similarity_score', 0):.3f}" for r in results[:3]]
                logger.debug(f"Top similarity scores: {top_similarities}")
            elif len(results) == 0:
                logger.warning(f"No movies found in semantic search. Returning empty list (no fallback to other sources).")
            
            return results
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Semantic search from Qdrant failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning empty list.")
            # Return empty list - NO fallback to other sources
            return []
    
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