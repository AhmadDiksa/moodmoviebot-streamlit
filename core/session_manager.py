"""
Session State Management
File: core/session_manager.py
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
import logging
from core.history_manager import HistoryManager

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage Streamlit session state"""
    
    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        
        # Chat messages
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Pending confirmation state
        if 'pending_confirmation' not in st.session_state:
            st.session_state.pending_confirmation = None
        
        # Current mood
        if 'current_mood' not in st.session_state:
            st.session_state.current_mood = None
        
        # Recommendations history
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = []
        
        # User preferences
        if 'preferred_genres' not in st.session_state:
            st.session_state.preferred_genres = []
        
        if 'disliked_genres' not in st.session_state:
            st.session_state.disliked_genres = []
        
        # Statistics
        if 'conversation_count' not in st.session_state:
            st.session_state.conversation_count = 0
        
        if 'total_movies_recommended' not in st.session_state:
            st.session_state.total_movies_recommended = 0
        
        # Session metadata
        if 'session_started_at' not in st.session_state:
            st.session_state.session_started_at = datetime.now()
        
        # History loaded flag
        if 'history_loaded' not in st.session_state:
            st.session_state.history_loaded = False
        
        logger.info("Session state initialized")
    
    @staticmethod
    def add_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add message to chat history
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata dictionary
        """
        logger.debug(f"Adding {role} message (length: {len(content)} chars)")
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            message['metadata'] = metadata
        
        st.session_state.messages.append(message)
        
        # Limit history size
        max_messages = 50
        if len(st.session_state.messages) > max_messages:
            removed = len(st.session_state.messages) - max_messages
            st.session_state.messages = st.session_state.messages[-max_messages:]
            logger.debug(f"Message history trimmed - removed {removed} old messages")
        
        # Auto-save to file
        try:
            HistoryManager.save_history(
                st.session_state.messages,
                metadata={
                    "total_messages": len(st.session_state.messages),
                    "session_id": str(id(st.session_state))
                }
            )
        except Exception as e:
            logger.warning(f"Failed to auto-save history: {e}")
        
        logger.debug(f"Total messages in history: {len(st.session_state.messages)}")
    
    @staticmethod
    def update_mood(mood_data: Dict[str, Any]):
        """
        Update current mood
        
        Args:
            mood_data: Mood analysis result
        """
        st.session_state.current_mood = mood_data
        logger.info(f"Mood updated: {mood_data.get('detected_moods', [])}")
    
    @staticmethod
    def add_recommendations(movies: List[Dict]):
        """
        Add movie recommendations
        
        IMPORTANT: Only movies with valid raw_payload from Qdrant will be saved.
        Movies without raw_payload will be filtered out.
        
        Args:
            movies: List of movie dictionaries (must have raw_payload from Qdrant)
        """
        if not movies:
            logger.warning("Empty movie list provided to add_recommendations. Nothing to add.")
            return
        
        # Validate that all movies have raw_payload from Qdrant
        valid_movies = []
        invalid_count = 0
        
        for movie in movies:
            # Validate movie is a dict
            if not isinstance(movie, dict):
                logger.warning(f"Invalid movie type: {type(movie)}. Skipping.")
                invalid_count += 1
                continue
            
            # Validate movie has raw_payload (proof it comes from Qdrant)
            if not movie.get('raw_payload'):
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' missing raw_payload from Qdrant. Filtering out.")
                invalid_count += 1
                continue
            
            # Validate raw_payload is a dict
            raw_payload = movie.get('raw_payload')
            if not isinstance(raw_payload, dict):
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' has invalid raw_payload type: {type(raw_payload)}. Filtering out.")
                invalid_count += 1
                continue
            
            # Validate movie has title
            if not movie.get('title'):
                logger.warning(f"Movie missing title field. Filtering out.")
                invalid_count += 1
                continue
            
            # Validate movie has tmdb_id (required field from Qdrant database)
            tmdb_id = movie.get('tmdb_id') or raw_payload.get('tmdb_id')
            if not tmdb_id:
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' missing tmdb_id from Qdrant. Filtering out.")
                invalid_count += 1
                continue
            
            valid_movies.append(movie)
        
        if invalid_count > 0:
            logger.warning(f"Filtered out {invalid_count} invalid movies. Only {len(valid_movies)} valid movies from Qdrant will be saved.")
        
        if not valid_movies:
            logger.error("No valid movies from Qdrant to save. All movies were filtered out.")
            st.session_state.recommendations = []
            return
        
        # Save only valid movies from Qdrant
        st.session_state.recommendations = valid_movies
        st.session_state.total_movies_recommended += len(valid_movies)
        logger.info(f"Added {len(valid_movies)} validated recommendations from Qdrant (filtered out {invalid_count} invalid movies)")
    
    @staticmethod
    def update_preferences(
        liked: Optional[List[str]] = None,
        disliked: Optional[List[str]] = None
    ):
        """
        Update user genre preferences
        
        Args:
            liked: Genres user likes
            disliked: Genres user dislikes
        """
        if liked is not None:
            st.session_state.preferred_genres = list(set(liked))
            logger.info(f"Updated liked genres: {liked}")
        
        if disliked is not None:
            st.session_state.disliked_genres = list(set(disliked))
            logger.info(f"Updated disliked genres: {disliked}")
    
    @staticmethod
    def increment_conversation():
        """Increment conversation counter"""
        st.session_state.conversation_count += 1
    
    @staticmethod
    def clear_chat():
        """Clear chat history"""
        st.session_state.messages = []
        st.session_state.conversation_count = 0
        st.session_state.pending_confirmation = None
        
        # Clear history file
        try:
            HistoryManager.clear_history()
        except Exception as e:
            logger.warning(f"Failed to clear history file: {e}")
        
        logger.info("Chat history cleared")
    
    @staticmethod
    def reset_profile():
        """Reset user profile"""
        st.session_state.current_mood = None
        st.session_state.recommendations = []
        st.session_state.preferred_genres = []
        st.session_state.disliked_genres = []
        st.session_state.pending_confirmation = None
        logger.info("User profile reset")
    
    @staticmethod
    def load_from_file() -> bool:
        """
        Load chat history from file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if st.session_state.get('history_loaded', False):
            logger.debug("History already loaded, skipping")
            return True
        
        try:
            history_data = HistoryManager.load_history()
            
            if history_data is None:
                logger.debug("No history file found, starting fresh")
                st.session_state.history_loaded = True
                return True
            
            messages = history_data.get("messages", [])
            
            if messages:
                st.session_state.messages = messages
                logger.info(f"Loaded {len(messages)} messages from history file")
            
            st.session_state.history_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load history from file: {e}")
            st.session_state.history_loaded = True  # Mark as loaded to prevent retry loops
            return False
    
    @staticmethod
    def save_to_file() -> bool:
        """
        Save chat history to file
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            return HistoryManager.save_history(
                st.session_state.messages,
                metadata={
                    "total_messages": len(st.session_state.messages),
                    "session_id": str(id(st.session_state))
                }
            )
        except Exception as e:
            logger.error(f"Failed to save history to file: {e}")
            return False
    
    @staticmethod
    def set_pending_confirmation(confirmation_data: Dict[str, Any]):
        """
        Set pending confirmation data
        
        Args:
            confirmation_data: Dictionary with confirmation info (genres, mood, etc.)
        """
        st.session_state.pending_confirmation = confirmation_data
        logger.debug(f"Pending confirmation set: {confirmation_data}")
    
    @staticmethod
    def clear_pending_confirmation():
        """Clear pending confirmation"""
        st.session_state.pending_confirmation = None
        logger.debug("Pending confirmation cleared")
    
    @staticmethod
    def get_pending_confirmation() -> Optional[Dict[str, Any]]:
        """
        Get pending confirmation data
        
        Returns:
            Confirmation data dictionary or None
        """
        return st.session_state.get('pending_confirmation')
    
    @staticmethod
    def get_context_summary() -> str:
        """
        Get context summary for LLM
        
        Returns:
            String summary of current context
        """
        parts = []
        
        # Current mood
        if st.session_state.current_mood:
            moods = st.session_state.current_mood.get('detected_moods', [])
            if moods:
                parts.append(f"Current mood: {', '.join(moods)}")
        
        # Preferences
        if st.session_state.preferred_genres:
            parts.append(f"Liked genres: {', '.join(st.session_state.preferred_genres)}")
        
        if st.session_state.disliked_genres:
            parts.append(f"Disliked genres: {', '.join(st.session_state.disliked_genres)}")
        
        # Conversation count
        if st.session_state.conversation_count > 0:
            parts.append(f"Conversation turns: {st.session_state.conversation_count}")
        
        return " | ".join(parts) if parts else "New conversation"
    
    @staticmethod
    def export_data() -> Dict[str, Any]:
        """
        Export all session data
        
        Returns:
            Dictionary with all session data
        """
        return {
            'messages': st.session_state.messages,
            'current_mood': st.session_state.current_mood,
            'recommendations': st.session_state.recommendations,
            'preferred_genres': st.session_state.preferred_genres,
            'disliked_genres': st.session_state.disliked_genres,
            'statistics': {
                'conversation_count': st.session_state.conversation_count,
                'total_movies_recommended': st.session_state.total_movies_recommended,
                'session_started_at': st.session_state.session_started_at.isoformat()
            }
        }
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Get session statistics
        
        Returns:
            Dictionary with session stats
        """
        session_duration = datetime.now() - st.session_state.session_started_at
        
        return {
            'conversation_count': st.session_state.conversation_count,
            'total_messages': len(st.session_state.messages),
            'total_recommendations': st.session_state.total_movies_recommended,
            'current_recommendations': len(st.session_state.recommendations),
            'preferred_genres_count': len(st.session_state.preferred_genres),
            'disliked_genres_count': len(st.session_state.disliked_genres),
            'has_mood': st.session_state.current_mood is not None,
            'session_duration_minutes': int(session_duration.total_seconds() / 60)
        }