"""
Context Manager for Building Conversation Context
File: core/context_manager.py

Builds context from chat history and user preferences for LLM
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextManager:
    """Manage conversation context building"""
    
    @staticmethod
    def build_conversation_context(max_messages: int = 10) -> str:
        """
        Build conversation context from history for LLM
        
        Args:
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted context string
        """
        if 'messages' not in st.session_state or not st.session_state.messages:
            return ""
        
        messages = st.session_state.messages[-max_messages:]
        
        context_lines = []
        context_lines.append("Konteks percakapan sebelumnya:")
        context_lines.append("=" * 50)
        
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "user":
                context_lines.append(f"User: {content[:300]}")  # Limit length
            elif role == "assistant":
                # Extract text content (exclude movie recommendations)
                text_content = content
                if "**Mood Analysis:**" in text_content:
                    # Extract only mood analysis part
                    parts = text_content.split("**Recommendations:**")
                    text_content = parts[0].strip()
                
                context_lines.append(f"Assistant: {text_content[:300]}")
        
        context_lines.append("=" * 50)
        context_lines.append("\nGunakan konteks percakapan sebelumnya untuk memahami follow-up question atau perubahan mood pengguna.")
        
        return "\n".join(context_lines)
    
    @staticmethod
    def get_user_preferences_summary() -> str:
        """
        Get summary of user preferences from session state
        
        Returns:
            Formatted preferences summary
        """
        parts = []
        
        # Preferred genres
        if st.session_state.get('preferred_genres'):
            genres = ', '.join(st.session_state.preferred_genres)
            parts.append(f"Genre favorit: {genres}")
        
        # Disliked genres
        if st.session_state.get('disliked_genres'):
            genres = ', '.join(st.session_state.disliked_genres)
            parts.append(f"Genre yang tidak disukai: {genres}")
        
        # Current mood
        if st.session_state.get('current_mood'):
            mood = st.session_state.current_mood
            moods = mood.get('detected_moods', [])
            if moods:
                parts.append(f"Mood saat ini: {', '.join(moods)}")
        
        return " | ".join(parts) if parts else "Belum ada preferensi"
    
    @staticmethod
    def get_recommended_movies_history() -> List[Dict[str, Any]]:
        """
        Get list of movies that have been recommended previously
        
        Returns:
            List of movie dictionaries that were recommended
        """
        recommended_movies = []
        
        # Check current recommendations
        if st.session_state.get('recommendations'):
            recommended_movies.extend(st.session_state.recommendations)
        
        # Check message history for movie recommendations
        if 'messages' not in st.session_state:
            return recommended_movies
        
        for msg in st.session_state.messages:
            if msg.get("role") == "assistant":
                metadata = msg.get("metadata", {})
                if metadata.get("type") == "recommendation":
                    movies = metadata.get("movies", [])
                    recommended_movies.extend(movies)
        
        return recommended_movies
    
    @staticmethod
    def get_recommended_movie_ids() -> Set[int]:
        """
        Get set of movie TMDB IDs that have been recommended
        
        Returns:
            Set of TMDB IDs from Qdrant database
        """
        movie_ids = set()
        
        movies = ContextManager.get_recommended_movies_history()
        for movie in movies:
            # Use tmdb_id from database (primary identifier)
            tmdb_id = None
            
            # First try to get from movie dict directly
            if movie.get('tmdb_id'):
                tmdb_id = movie.get('tmdb_id')
            # Then try from raw_payload (from Qdrant)
            elif movie.get('raw_payload') and isinstance(movie.get('raw_payload'), dict):
                tmdb_id = movie.get('raw_payload', {}).get('tmdb_id')
            
            if tmdb_id:
                try:
                    movie_ids.add(int(tmdb_id))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid tmdb_id: {tmdb_id} for movie {movie.get('title', 'Unknown')}")
        
        return movie_ids
    
    @staticmethod
    def should_exclude_movie(movie: Dict[str, Any]) -> bool:
        """
        Check if a movie should be excluded (already recommended)
        
        Uses tmdb_id as primary identifier for matching (from Qdrant database).
        Falls back to title matching if tmdb_id not available.
        
        Args:
            movie: Movie dictionary from Qdrant
            
        Returns:
            True if movie should be excluded, False otherwise
        """
        recommended_ids = ContextManager.get_recommended_movie_ids()
        
        # Primary check: Use tmdb_id from database
        tmdb_id = None
        if movie.get('tmdb_id'):
            tmdb_id = movie.get('tmdb_id')
        elif isinstance(movie, dict) and movie.get('raw_payload') and isinstance(movie.get('raw_payload'), dict):
            # Try from raw_payload if not in main dict
            tmdb_id = movie.get('raw_payload', {}).get('tmdb_id')
        
        if tmdb_id:
            try:
                if int(tmdb_id) in recommended_ids:
                    logger.debug(f"Movie with tmdb_id {tmdb_id} already recommended. Excluding.")
                    return True
            except (ValueError, TypeError):
                logger.warning(f"Invalid tmdb_id: {tmdb_id} for movie {movie.get('title', 'Unknown')}")
        
        # Fallback: Check by title (fuzzy match) if tmdb_id not available
        movie_title = movie.get('title', '').lower().strip()
        if not movie_title:
            return False
        
        recommended_movies = ContextManager.get_recommended_movies_history()
        for rec_movie in recommended_movies:
            rec_title = rec_movie.get('title', '').lower().strip()
            if rec_title and movie_title == rec_title:
                logger.debug(f"Movie '{movie_title}' already recommended (title match). Excluding.")
                return True
        
        return False
    
    @staticmethod
    def build_full_context(user_input: str, include_preferences: bool = True, include_history: bool = True) -> str:
        """
        Build full context string for LLM
        
        Args:
            user_input: Current user input
            include_preferences: Whether to include user preferences
            include_history: Whether to include conversation history
            
        Returns:
            Full context string
        """
        context_parts = []
        
        # Conversation history
        if include_history:
            history_context = ContextManager.build_conversation_context()
            if history_context:
                context_parts.append(history_context)
        
        # User preferences
        if include_preferences:
            prefs = ContextManager.get_user_preferences_summary()
            if prefs != "Belum ada preferensi":
                context_parts.append(f"\nPreferensi pengguna: {prefs}")
        
        # Current input
        context_parts.append(f"\nInput pengguna saat ini: {user_input}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def get_conversation_summary() -> Dict[str, Any]:
        """
        Get summary of current conversation
        
        Returns:
            Dictionary with conversation summary
        """
        messages = st.session_state.get('messages', [])
        
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        
        # Count recommendations
        recommendation_count = 0
        for msg in assistant_messages:
            metadata = msg.get('metadata', {})
            if metadata.get('type') == 'recommendation':
                recommendation_count += 1
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'recommendations_given': recommendation_count,
            'has_history': len(messages) > 0
        }

