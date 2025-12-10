"""
Session State Management
File: core/session_manager.py
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage Streamlit session state"""
    
    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        
        # Chat messages
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
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
        
        logger.info("Session state initialized")
    
    @staticmethod
    def add_message(role: str, content: str):
        """
        Add message to chat history
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        logger.debug(f"Adding {role} message (length: {len(content)} chars)")
        st.session_state.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit history size
        max_messages = 50
        if len(st.session_state.messages) > max_messages:
            removed = len(st.session_state.messages) - max_messages
            st.session_state.messages = st.session_state.messages[-max_messages:]
            logger.debug(f"Message history trimmed - removed {removed} old messages")
        
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
        
        Args:
            movies: List of movie dictionaries
        """
        st.session_state.recommendations = movies
        st.session_state.total_movies_recommended += len(movies)
        logger.info(f"Added {len(movies)} recommendations")
    
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
        logger.info("Chat history cleared")
    
    @staticmethod
    def reset_profile():
        """Reset user profile"""
        st.session_state.current_mood = None
        st.session_state.recommendations = []
        st.session_state.preferred_genres = []
        st.session_state.disliked_genres = []
        logger.info("User profile reset")
    
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