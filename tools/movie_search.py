"""
Movie Search Tool
File: tools/movie_search.py
"""

import logging
import streamlit as st
from typing import List, Dict, Any, Optional
from core.qdrant_manager import QdrantManager
from core.embedding_manager import get_embedding_manager
from utils.genre_utils import genre_names_to_ids, genre_ids_to_names
from utils.cache_utils import StreamlitCache
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class MovieSearcher:
    """
    Search and rank movies
    
    IMPORTANT: This class ONLY searches movies from Qdrant database.
    No external APIs (TMDB, OMDB, etc.) are used. All movie data comes from Qdrant.
    """
    
    def __init__(self, qdrant_manager: QdrantManager):
        """
        Initialize Movie Searcher
        
        Args:
            qdrant_manager: Qdrant Manager instance (REQUIRED - no fallback to other sources)
        
        Raises:
            ValueError: If qdrant_manager is None
        """
        if qdrant_manager is None:
            raise ValueError("QdrantManager is required. Movie search ONLY uses Qdrant database.")
        self.qdrant_manager = qdrant_manager
        logger.info("MovieSearcher initialized - ONLY using Qdrant database for movie search")
    
    def search_by_genres(
        self, 
        genre_names: List[str],
        limit: int = 5,
        personalize: bool = True,
        context_hash: str = None,
        query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search movies by genre names using hybrid search (semantic + filter)
        
        IMPORTANT: This method ONLY searches Qdrant database. No external APIs are used.
        Uses semantic search if query_text is provided, otherwise falls back to filter-based search.
        If Qdrant fails, returns empty list. No fallback to other sources.
        
        Args:
            genre_names: List of genre names (e.g., ["Action", "Comedy"])
            limit: Maximum number of results to return
            personalize: Apply user preferences for ranking
            context_hash: Optional hash of user input/context for cache key uniqueness
            query_text: Optional query text for semantic search (user input + mood description)
        
        Returns:
            List of movie dictionaries with scores (empty list if Qdrant fails)
        """
        import time
        import hashlib
        start_time = time.time()
        
        # Validate that qdrant_manager is available
        if self.qdrant_manager is None:
            logger.error("QdrantManager is None - cannot search movies. Movie search ONLY uses Qdrant.")
            return []
        
        logger.info(f"Searching movies from Qdrant ONLY - Genres: {genre_names}, Limit: {limit}, Personalize: {personalize}")
        if query_text:
            logger.info(f"Using hybrid search (semantic + filter) with query text")
        logger.debug("IMPORTANT: Movie search uses ONLY Qdrant database. No external APIs (TMDB, OMDB, etc.)")
        
        try:
            # Create cache key with context hash for uniqueness
            # Include context_hash and query_text to ensure different contexts get different results
            if context_hash:
                if query_text:
                    cache_key = f"semantic-{'-'.join(sorted(genre_names))}-{limit}-{context_hash}"
                else:
                    cache_key = f"{'-'.join(sorted(genre_names))}-{limit}-{context_hash}"
            else:
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
            
            # Try semantic search if query_text is provided
            movies = []
            use_semantic = query_text and query_text.strip()
            
            if use_semantic:
                try:
                    logger.debug("Attempting semantic search with embedding...")
                    # Get embedding manager
                    config = AppConfig.load_from_secrets()
                    embedding_manager = get_embedding_manager(config)
                    
                    # Encode query text to vector
                    query_vector = embedding_manager.encode_query(query_text)
                    
                    if query_vector:
                        logger.debug(f"Query encoded to vector (dim: {len(query_vector)})")
                        # Perform semantic search with genre filter
                        movies = self.qdrant_manager.search_by_semantic(
                            query_vector=query_vector,
                            genre_ids=genre_ids,
                            limit=100
                        )
                        logger.debug(f"Semantic search returned {len(movies)} movies")
                    else:
                        logger.warning("Failed to encode query text, falling back to filter-based search")
                        use_semantic = False
                except Exception as e:
                    logger.warning(f"Semantic search failed: {e}, falling back to filter-based search")
                    use_semantic = False
            
            # Fallback to filter-based search if semantic search not used or failed
            if not use_semantic:
                logger.debug("Using filter-based search (no semantic search)...")
                movies = self.qdrant_manager.search_by_genres(genre_ids, limit=100)
                logger.debug(f"Filter-based search returned {len(movies)} movies")
            
            if not movies:
                logger.warning("No movies found in Qdrant database. Returning empty list (no fallback to other sources).")
                return []
            
            # Get previously recommended movies to avoid duplicates
            previously_recommended = set()
            if st.session_state.get('recommendations'):
                for prev_movie in st.session_state.recommendations:
                    prev_title = prev_movie.get('title')
                    if prev_title:
                        previously_recommended.add(prev_title)
            
            if previously_recommended:
                logger.debug(f"Excluding {len(previously_recommended)} previously recommended movies")
            
            # Filter out previously recommended movies
            filtered_movies = [
                m for m in movies 
                if m.get('title') not in previously_recommended
            ]
            
            # If we filtered too many, use original list but log it
            if len(filtered_movies) < limit and len(movies) > len(filtered_movies):
                logger.debug(f"Only {len(filtered_movies)} movies after filtering, using original list")
                filtered_movies = movies
            
            logger.debug(f"After filtering duplicates: {len(filtered_movies)} movies available")
            
            # Score and rank (with semantic similarity if available)
            logger.debug(f"Scoring and ranking {len(filtered_movies)} movies...")
            scored_movies = self._score_and_rank(
                filtered_movies, 
                limit=limit,
                personalize=personalize,
                context_hash=context_hash,
                use_semantic_scores=use_semantic
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
            logger.error(f"Movie search from Qdrant failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning empty list.")
            logger.debug(f"Genre names that failed: {genre_names}")
            # Return empty list - NO fallback to other sources
            return []
    
    def _score_and_rank(
        self,
        movies: List[Dict[str, Any]],
        limit: int = 5,
        personalize: bool = True,
        context_hash: str = None,
        use_semantic_scores: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Score and rank movies from Qdrant
        
        IMPORTANT: Only movies with valid raw_payload (from Qdrant) will be recommended.
        Movies without raw_payload will be filtered out.
        
        Args:
            movies: List of movie payloads from Qdrant
            limit: Maximum number to return
            personalize: Apply personalization
            context_hash: Optional context hash for adding variation
            use_semantic_scores: Whether to use semantic similarity scores (from semantic search)
        
        Returns:
            Sorted list of movies with scores (only movies from Qdrant)
        """
        import random
        logger.debug(f"Scoring {len(movies)} movies from Qdrant (limit: {limit}, personalize: {personalize})")
        scored = []
        
        # Validate that all movies are from Qdrant (have valid data structure)
        valid_movies = []
        invalid_count = 0
        
        for movie in movies:
            # Validate movie has required fields from Qdrant
            if not isinstance(movie, dict):
                logger.warning(f"Invalid movie data type: {type(movie)}. Skipping.")
                invalid_count += 1
                continue
            
            # Check if movie has title (required field from Qdrant)
            if not movie.get('title'):
                logger.warning(f"Movie missing title field. Skipping. Movie data: {movie.keys()}")
                invalid_count += 1
                continue
            
            valid_movies.append(movie)
        
        if invalid_count > 0:
            logger.warning(f"Filtered out {invalid_count} invalid movies. Only {len(valid_movies)} valid movies from Qdrant will be scored.")
        
        if not valid_movies:
            logger.error("No valid movies from Qdrant to score. All movies were filtered out.")
            return []
        
        # Use context_hash to seed random for consistent but varied results
        if context_hash:
            try:
                # Use hash to create a seed for randomness
                seed = int(context_hash[:8], 16) if len(context_hash) >= 8 else hash(context_hash)
                random.seed(seed)
            except:
                pass
        
        for idx, movie in enumerate(valid_movies):
            # Semantic similarity score (if available from semantic search)
            semantic_score = 0.0
            if use_semantic_scores and movie.get('similarity_score') is not None:
                # Normalize similarity score (typically 0-1 for cosine similarity)
                # Scale to 0-10 range to match other scores
                similarity = movie.get('similarity_score', 0)
                semantic_score = similarity * 10.0  # Scale to 0-10
                logger.debug(f"Movie {idx+1}: {movie.get('title', 'Unknown')[:30]} - Semantic similarity: {similarity:.3f} (scaled: {semantic_score:.2f})")
            
            # Base score from ratings (if not using semantic scores as primary)
            rating = movie.get('vote_average', 0)
            popularity = movie.get('popularity', 0)
            vote_count = movie.get('vote_count', 0)
            
            # Calculate base score (rating-based)
            rating_score = (
                rating * 0.7 +
                (popularity * 0.003) +
                min(vote_count / 1000, 1.0) * 0.5
            )
            
            # Combine semantic and rating scores
            # Weight: 60% semantic similarity + 40% rating factors (if semantic available)
            if use_semantic_scores and semantic_score > 0:
                base_score = (semantic_score * 0.6) + (rating_score * 0.4)
            else:
                base_score = rating_score
            
            # Add small random variation to break ties and add diversity
            # This ensures different contexts get slightly different rankings
            variation = random.uniform(-0.1, 0.1) if context_hash else 0.0
            
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
                    logger.debug(f"Movie {idx+1}: {movie.get('title', 'Unknown')[:30]} - Base: {base_score:.2f}, Personalization: {personalization_score:.2f}, Variation: {variation:.2f}")
            
            # Final score with variation
            final_score = base_score + personalization_score + variation
            
            # IMPORTANT: Ensure raw_payload is set to original Qdrant payload
            # This is the proof that the movie comes from Qdrant
            raw_payload = movie  # The movie dict itself is the raw_payload from Qdrant
            
            # Validate that we have a valid raw_payload
            if not raw_payload or not isinstance(raw_payload, dict):
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' missing valid raw_payload from Qdrant. Skipping.")
                continue
            
            # Create result entry - ONLY movies from Qdrant with valid raw_payload
            # Include all fields from database: tmdb_id, original_title, poster_url, trailer_url
            scored.append({
                'title': movie.get('title', 'Unknown'),
                'original_title': movie.get('original_title', ''),
                'tmdb_id': movie.get('tmdb_id'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                'rating': rating,
                'popularity': popularity,
                'vote_count': vote_count,
                'genres': genre_ids_to_names(tuple(movie.get('genre_ids', []))),
                'overview': movie.get('overview', 'No description available'),
                'score': round(final_score, 2),
                'raw_payload': raw_payload  # Original Qdrant payload - REQUIRED for validation
            })
        
        # Sort by score (descending) and limit
        scored.sort(key=lambda x: x['score'], reverse=True)
        result = scored[:limit]
        
        # Final validation: Ensure all recommended movies have raw_payload from Qdrant
        validated_result = []
        for movie in result:
            if not movie.get('raw_payload'):
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' missing raw_payload. Filtering out.")
                continue
            validated_result.append(movie)
        
        if len(validated_result) < len(result):
            logger.warning(f"Filtered out {len(result) - len(validated_result)} movies without raw_payload. Only {len(validated_result)} valid movies from Qdrant will be returned.")
        
        if validated_result:
            top_scores = [f"{m['title'][:20]}: {m['score']:.2f}" for m in validated_result[:3]]
            logger.debug(f"Top scores (all from Qdrant): {top_scores}")
        
        return validated_result
    
    def search_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Search movie by TMDB ID from Qdrant ONLY
        
        IMPORTANT: This method ONLY searches Qdrant database. No external APIs are used.
        If movie not found in Qdrant, returns None. No fallback to other sources.
        
        Args:
            tmdb_id: TMDB ID of the movie
        
        Returns:
            Movie dictionary with all fields from Qdrant or None if not found
        """
        # Validate that qdrant_manager is available
        if self.qdrant_manager is None:
            logger.error("QdrantManager is None - cannot search by tmdb_id. Movie search ONLY uses Qdrant.")
            return None
        
        logger.debug(f"Searching movie by TMDB ID in Qdrant ONLY: {tmdb_id}")
        logger.debug("IMPORTANT: Movie search uses ONLY Qdrant database. No external APIs.")
        
        try:
            movie = self.qdrant_manager.get_movie_by_tmdb_id(tmdb_id)
            
            if not movie:
                logger.debug(f"Movie with tmdb_id {tmdb_id} not found in Qdrant database (no fallback to other sources)")
                return None
            
            # Format result with all fields from database
            return {
                'title': movie.get('title', 'Unknown'),
                'original_title': movie.get('original_title', ''),
                'tmdb_id': movie.get('tmdb_id'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                'rating': movie.get('vote_average', 0),
                'popularity': movie.get('popularity', 0),
                'vote_count': movie.get('vote_count', 0),
                'genres': genre_ids_to_names(tuple(movie.get('genre_ids', []))),
                'overview': movie.get('overview', 'No description available'),
                'raw_payload': movie  # Original Qdrant payload - REQUIRED for validation
            }
            
        except Exception as e:
            logger.error(f"TMDB ID search from Qdrant failed: {e}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning None.")
            # Return None - NO fallback to other sources
            return None
    
    def search_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Search movie by title from Qdrant ONLY
        
        IMPORTANT: This method ONLY searches Qdrant database. No external APIs are used.
        
        Args:
            title: Movie title
        
        Returns:
            Movie dictionary or None if not found in Qdrant (no fallback to other sources)
        """
        # Validate that qdrant_manager is available
        if self.qdrant_manager is None:
            logger.error("QdrantManager is None - cannot search by title. Movie search ONLY uses Qdrant.")
            return None
        
        logger.debug(f"Searching movie by title in Qdrant ONLY: {title}")
        
        try:
            movie = self.qdrant_manager.get_movie_by_title(title)
            
            if not movie:
                logger.debug(f"Movie '{title}' not found in Qdrant database (no fallback to other sources)")
                return None
            
            # Format result with all fields from database
            return {
                'title': movie.get('title', 'Unknown'),
                'original_title': movie.get('original_title', ''),
                'tmdb_id': movie.get('tmdb_id'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                'rating': movie.get('vote_average', 0),
                'popularity': movie.get('popularity', 0),
                'vote_count': movie.get('vote_count', 0),
                'genres': genre_ids_to_names(tuple(movie.get('genre_ids', []))),
                'overview': movie.get('overview', 'No description available'),
                'raw_payload': movie
            }
            
        except Exception as e:
            logger.error(f"Title search from Qdrant failed: {e}")
            logger.error("IMPORTANT: No fallback to external APIs. Returning None.")
            # Return None - NO fallback to other sources
            return None