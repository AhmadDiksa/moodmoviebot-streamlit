"""
Movie Search Tool
File: tools/movie_search.py
"""

import logging
import streamlit as st
from typing import List, Dict, Any
from core.qdrant_manager import QdrantManager
from utils.genre_utils import genre_names_to_ids, genre_ids_to_names
from utils.cache_utils import StreamlitCache

logger = logging.getLogger(__name__)

class MovieSearcher:
    """Search and rank movies"""
    
    def __init__(self, qdrant_manager: QdrantManager):
        """
        Initialize Movie Searcher
        
        Args:
            qdrant_manager: Qdrant Manager instance
        """
        self.qdrant_manager = qdrant_manager
    
    def search_by_genres(
        self, 
        genre_names: List[str],
        limit: int = 5,
        personalize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search movies by genre names
        
        Args:
            genre_names: List of genre names (e.g., ["Action", "Comedy"])
            limit: Maximum number of results to return
            personalize: Apply user preferences for ranking
        
        Returns:
            List of movie dictionaries with scores
        """
        import time
        start_time = time.time()
        
        logger.info(f"Searching movies - Genres: {genre_names}, Limit: {limit}, Personalize: {personalize}")
        
        try:
            # Check cache first
            cache_key = f"{'-'.join(sorted(genre_names))}-{limit}"
            logger.debug(f"Checking cache with key: {cache_key}")
            cached = StreamlitCache.get("movie_search", cache_key)
            if cached and not personalize:
                duration = time.time() - start_time
                logger.info(f"Using cached search results (retrieved in {duration:.3f}s)")
                logger.debug(f"Cached results count: {len(cached)}")
                return cached
            
            # Convert genre names to IDs
            logger.debug(f"Converting genre names to IDs: {genre_names}")
            genre_ids = genre_names_to_ids(tuple(genre_names))
            logger.debug(f"Converted to genre IDs: {genre_ids}")
            
            if not genre_ids:
                logger.warning(f"No valid genre IDs for: {genre_names}")
                return []
            
            # Search in Qdrant
            logger.debug("Searching in Qdrant database...")
            movies = self.qdrant_manager.search_by_genres(genre_ids, limit=100)
            logger.debug(f"Qdrant returned {len(movies)} movies")
            
            if not movies:
                logger.warning("No movies found in database")
                return []
            
            # Score and rank
            logger.debug(f"Scoring and ranking {len(movies)} movies...")
            scored_movies = self._score_and_rank(
                movies, 
                limit=limit,
                personalize=personalize
            )
            logger.debug(f"Ranked to {len(scored_movies)} movies")
            
            # Cache results (only if not personalized)
            if not personalize and scored_movies:
                logger.debug("Caching search results...")
                StreamlitCache.set("movie_search", scored_movies, 3600, cache_key)
            
            duration = time.time() - start_time
            logger.info(f"Found {len(scored_movies)} movies in {duration:.2f}s")
            if scored_movies:
                logger.debug(f"Top movie: {scored_movies[0].get('title')} (score: {scored_movies[0].get('score')})")
            
            return scored_movies
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Movie search failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.debug(f"Genre names that failed: {genre_names}")
            return []
    
    def _score_and_rank(
        self,
        movies: List[Dict[str, Any]],
        limit: int = 5,
        personalize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Score and rank movies
        
        Args:
            movies: List of movie payloads from Qdrant
            limit: Maximum number to return
            personalize: Apply personalization
        
        Returns:
            Sorted list of movies with scores
        """
        logger.debug(f"Scoring {len(movies)} movies (limit: {limit}, personalize: {personalize})")
        scored = []
        
        for idx, movie in enumerate(movies):
            # Base score from ratings
            rating = movie.get('vote_average', 0)
            popularity = movie.get('popularity', 0)
            vote_count = movie.get('vote_count', 0)
            
            # Calculate base score
            base_score = (
                rating * 0.7 +
                (popularity * 0.003) +
                min(vote_count / 1000, 1.0) * 0.5
            )
            
            # Personalization bonus/penalty
            personalization_score = 0.0
            
            if personalize:
                movie_genre_ids = movie.get('genre_ids', [])
                movie_genres = set(genre_ids_to_names(tuple(movie_genre_ids)))
                
                # Get user preferences
                preferred = set(st.session_state.get('preferred_genres', []))
                disliked = set(st.session_state.get('disliked_genres', []))
                
                # Calculate personalization
                preferred_match = len(movie_genres & preferred)
                disliked_match = len(movie_genres & disliked)
                
                personalization_score = (preferred_match * 0.5) - (disliked_match * 0.8)
                
                if idx < 3:  # Log first 3 for debugging
                    logger.debug(f"Movie {idx+1}: {movie.get('title', 'Unknown')[:30]} - Base: {base_score:.2f}, Personalization: {personalization_score:.2f}")
            
            # Final score
            final_score = base_score + personalization_score
            
            # Create result entry
            scored.append({
                'title': movie.get('title', 'Unknown'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                'rating': rating,
                'popularity': popularity,
                'vote_count': vote_count,
                'genres': genre_ids_to_names(tuple(movie.get('genre_ids', []))),
                'overview': movie.get('overview', 'No description available'),
                'score': round(final_score, 2),
                'raw_payload': movie  # Keep original for detail view
            })
        
        # Sort by score (descending) and limit
        scored.sort(key=lambda x: x['score'], reverse=True)
        result = scored[:limit]
        
        if result:
            top_scores = [f"{m['title'][:20]}: {m['score']:.2f}" for m in result[:3]]
            logger.debug(f"Top scores: {top_scores}")
        
        return result
    
    def search_by_title(self, title: str) -> Dict[str, Any]:
        """
        Search movie by title
        
        Args:
            title: Movie title
        
        Returns:
            Movie dictionary or None if not found
        """
        try:
            movie = self.qdrant_manager.get_movie_by_title(title)
            
            if not movie:
                return None
            
            # Format result
            return {
                'title': movie.get('title', 'Unknown'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                'rating': movie.get('vote_average', 0),
                'popularity': movie.get('popularity', 0),
                'vote_count': movie.get('vote_count', 0),
                'genres': genre_ids_to_names(tuple(movie.get('genre_ids', []))),
                'overview': movie.get('overview', 'No description available'),
                'raw_payload': movie
            }
            
        except Exception as e:
            logger.error(f"Title search failed: {e}")
            return None