"""
Chat UI Components
File: ui/chat_components.py

Reusable components for chatbot interface
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from ui.components import display_movie_card
from utils.genre_utils import get_genre_emoji

def render_chat_message(message: Dict[str, Any], show_timestamp: bool = False):
    """
    Render a chat message with better styling
    
    Args:
        message: Message dictionary with role, content, timestamp
        show_timestamp: Whether to show timestamp
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    timestamp = message.get("timestamp", "")
    metadata = message.get("metadata", {})
    
    with st.chat_message(role):
        # Display content
        st.markdown(content)
        
        # Display timestamp if requested
        if show_timestamp and timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                st.caption(f"🕐 {dt.strftime('%H:%M')}")
            except:
                pass
        
        # Display movie recommendations if present
        if metadata.get("type") == "recommendation":
            movies = metadata.get("movies", [])
            if movies:
                st.markdown("---")
                for idx, movie in enumerate(movies, 1):
                    display_movie_card(movie, idx)
                    if movie.get('review_summary'):
                        st.markdown(f"**💬 Netizen:** {movie.get('review_summary')}")
                    if idx < len(movies):
                        st.markdown("---")

def render_movie_recommendation(movies: List[Dict[str, Any]], start_index: int = 1):
    """
    Render movie recommendations in chat format
    
    Args:
        movies: List of movie dictionaries
        start_index: Starting index for numbering
    """
    if not movies:
        st.info("Tidak ada film yang ditemukan.")
        return
    
    st.markdown("### 🎬 Rekomendasi Film")
    
    for idx, movie in enumerate(movies, start_index):
        display_movie_card(movie, idx)
        
        if movie.get('review_summary'):
            st.markdown(f"**💬 Netizen:** {movie.get('review_summary')}")
        
        if idx < len(movies) + start_index - 1:
            st.markdown("---")

def render_confirmation_prompt(genres: List[str], mood_summary: str = ""):
    """
    Render confirmation prompt asking user if they want recommendations
    
    Args:
        genres: List of recommended genres
        mood_summary: Optional mood summary text
    """
    # Format genres with emojis
    genre_text = ", ".join([f"{get_genre_emoji(g)} {g}" for g in genres])
    
    confirmation_text = f"Berdasarkan mood Anda"
    if mood_summary:
        confirmation_text += f" ({mood_summary})"
    confirmation_text += f", saya bisa merekomendasikan film dengan genre: **{genre_text}**.\n\n"
    confirmation_text += "Apakah Anda ingin melihat rekomendasi film?"
    
    st.markdown(confirmation_text)
    
    # Add quick action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Ya, tampilkan", key="confirm_yes", use_container_width=True):
            st.session_state.confirmation_response = "yes"
            st.rerun()
    
    with col2:
        if st.button("❌ Tidak", key="confirm_no", use_container_width=True):
            st.session_state.confirmation_response = "no"
            st.rerun()
    
    with col3:
        if st.button("🔄 Ubah Genre", key="confirm_change", use_container_width=True):
            st.session_state.confirmation_response = "change"
            st.rerun()

def render_mood_analysis_inline(mood_result: Dict[str, Any]):
    """
    Render mood analysis inline in chat
    
    Args:
        mood_result: Mood analysis result dictionary
    """
    moods = mood_result.get('detected_moods', [])
    intensity = mood_result.get('intensity_score', 0)
    summary = mood_result.get('summary', '')
    emotion_type = mood_result.get('emotion_type', 'neutral')
    
    # Emoji based on emotion type
    emoji_map = {
        'positive': '😊',
        'negative': '😔',
        'neutral': '😐',
        'mixed': '😌'
    }
    emoji = emoji_map.get(emotion_type, '🎭')
    
    st.markdown(f"### {emoji} Analisis Mood")
    st.markdown(f"**Mood terdeteksi:** {', '.join(moods)}")
    st.progress(intensity / 100)
    st.caption(f"Intensitas: {intensity}%")
    
    if summary:
        st.markdown(f"*{summary}*")

def render_loading_message(message: str = "Memproses..."):
    """
    Render loading message in chat
    
    Args:
        message: Loading message text
    """
    with st.chat_message("assistant"):
        with st.spinner(message):
            st.markdown("⏳ " + message)

def render_error_message(error: str, suggestion: str = ""):
    """
    Render error message in chat
    
    Args:
        error: Error message
        suggestion: Optional suggestion text
    """
    st.error(f"❌ {error}")
    if suggestion:
        st.info(f"💡 {suggestion}")

def render_welcome_message():
    """
    Render welcome message for new users
    """
    welcome_text = """
    👋 **Selamat datang di MoodMovieBot!**
    
    Saya adalah asisten AI yang akan membantu Anda menemukan film yang sesuai dengan mood Anda.
    
    **Cara menggunakan:**
    1. Ceritakan bagaimana perasaan Anda hari ini
    2. Saya akan menganalisis mood Anda
    3. Saya akan menanyakan apakah Anda ingin melihat rekomendasi film
    4. Nikmati film yang direkomendasikan!
    
    **Contoh:** "Saya sedang sedih hari ini" atau "Saya merasa senang dan ingin menonton film lucu"
    """
    
    with st.chat_message("assistant"):
        st.markdown(welcome_text)

def parse_confirmation_response(user_input: str) -> Optional[str]:
    """
    Parse user response to confirmation prompt
    
    Args:
        user_input: User's text input
        
    Returns:
        'yes', 'no', 'change', or None if unclear
    """
    user_lower = user_input.lower().strip()
    
    # Positive responses
    positive_keywords = ['ya', 'yup', 'yes', 'ok', 'oke', 'baik', 'silahkan', 'tampilkan', 'cari', 'mau', 'ingin']
    if any(keyword in user_lower for keyword in positive_keywords):
        return "yes"
    
    # Negative responses
    negative_keywords = ['tidak', 'no', 'nope', 'skip', 'lewati', 'tidak mau', 'enggak']
    if any(keyword in user_lower for keyword in negative_keywords):
        return "no"
    
    # Change request
    change_keywords = ['ubah', 'ganti', 'change', 'lain', 'beda', 'bisa', 'boleh']
    if any(keyword in user_lower for keyword in change_keywords):
        return "change"
    
    # Check if user is requesting specific genre
    genre_keywords = ['action', 'comedy', 'drama', 'horror', 'romance', 'thriller', 'sci-fi', 'fantasy']
    if any(keyword in user_lower for keyword in genre_keywords):
        return "change"
    
    return None

