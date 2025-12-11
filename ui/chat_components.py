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
    confirmation_text += "Apakah Anda ingin melihat rekomendasi film? Silakan ketik 'ya' untuk melihat rekomendasi, 'tidak' untuk membatalkan, atau 'ubah' untuk mengubah genre."
    
    st.markdown(confirmation_text)

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

def is_new_search_request(user_input: str) -> bool:
    """
    Detect if user is requesting a new movie search (not responding to confirmation)
    
    Args:
        user_input: User's text input
        
    Returns:
        True if user is requesting a new search, False otherwise
    """
    user_lower = user_input.lower().strip()
    
    # Patterns that indicate a new search request
    new_search_patterns = [
        'cari film lain',
        'cari lagi',
        'film lain',
        'rekomendasi lain',
        'yang lain',
        'cari yang lain',
        'cari film lainnya',
        'film lainnya',
        'rekomendasi lainnya',
        'cari lagi film',
        'cari film baru',
        'film baru',
        'rekomendasi baru',
        'cari film yang lain',
        'tolong cari',
        'bisa cari',
        'bisa cari film',
        'cari film',
        'cari lagi film',
        'cari film lain dong',
        'cari film lain lagi'
    ]
    
    # Check if input matches any new search pattern
    for pattern in new_search_patterns:
        if pattern in user_lower:
            return True
    
    return False

def parse_confirmation_response(user_input: str) -> Optional[str]:
    """
    Parse user response to confirmation prompt
    
    Args:
        user_input: User's text input
        
    Returns:
        'yes', 'no', 'change', or None if unclear
    """
    user_lower = user_input.lower().strip()
    
    # Check if this is a new search request first (should not be treated as confirmation)
    if is_new_search_request(user_input):
        return None
    
    # Positive responses (removed 'cari' to avoid conflict with new search requests)
    # Only accept 'cari' if it's clearly a confirmation like "ya, cari" or "cari saja"
    positive_keywords = ['ya', 'yup', 'yes', 'ok', 'oke', 'baik', 'silahkan', 'tampilkan', 'mau', 'ingin']
    if any(keyword in user_lower for keyword in positive_keywords):
        return "yes"
    
    # Special case: "cari" alone or with confirmation words
    if 'cari' in user_lower:
        # Only treat as "yes" if it's clearly a confirmation (short response)
        if len(user_lower.split()) <= 3 and any(word in user_lower for word in ['ya', 'ok', 'oke', 'baik', 'saja', 'sih']):
            return "yes"
        # Otherwise, it's likely a new search request (handled by is_new_search_request above)
    
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

def render_tool_status(tool_name: str, is_active: bool = True) -> str:
    """
    Render tool status badge HTML
    
    Args:
        tool_name: Name of the tool (e.g., "Mood Analyzer", "Movie Search")
        is_active: Whether the tool is currently active
        
    Returns:
        HTML string for tool status badge
    """
    # Tool icon mapping
    tool_icons = {
        "Mood Analyzer": "🤔",
        "Movie Search": "🔍",
        "Review Summarizer": "📝",
        "Preparing": "⚙️"
    }
    
    icon = tool_icons.get(tool_name, "🔄")
    active_class = "active" if is_active else ""
    
    return f"""
    <div class="tool-status-badge {active_class}">
        <span class="tool-icon">{icon}</span>
        <span class="tool-name">{tool_name}</span>
    </div>
    """

def render_loading_with_status(tool_name: str, status_message: str, show_spinner: bool = True):
    """
    Render loading indicator with tool name and status message
    
    Args:
        tool_name: Name of the tool being used
        status_message: Status message describing what's happening
        show_spinner: Whether to show spinner
    """
    # Tool icon mapping
    tool_icons = {
        "Mood Analyzer": "🤔",
        "Movie Search": "🔍",
        "Review Summarizer": "📝",
        "Preparing": "⚙️"
    }
    
    icon = tool_icons.get(tool_name, "🔄")
    
    # Create loading container HTML
    loading_html = f"""
    <div class="loading-container">
        <div class="tool-status-badge active">
            <span class="tool-icon">{icon}</span>
            <span class="tool-name">{tool_name}</span>
            <span class="status-message">- {status_message}</span>
        </div>
        <div class="gradient-loading-bar"></div>
    </div>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)
    
    if show_spinner:
        with st.spinner(""):
            # Empty spinner to show loading state
            pass

def render_progress_steps(current_step: int, total_steps: int, step_names: List[str]):
    """
    Render progress steps indicator
    
    Args:
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps
        step_names: List of step names
    """
    if len(step_names) != total_steps:
        # Pad or truncate step names
        step_names = step_names[:total_steps] + [f"Step {i+1}" for i in range(len(step_names), total_steps)]
    
    steps_html = '<div class="progress-steps">'
    
    for i in range(1, total_steps + 1):
        step_class = "progress-step"
        if i < current_step:
            step_class += " completed"
        elif i == current_step:
            step_class += " active"
        
        step_name = step_names[i-1] if i <= len(step_names) else f"Step {i}"
        steps_html += f'<div class="{step_class}">{step_name}</div>'
    
    steps_html += '</div>'
    
    st.markdown(steps_html, unsafe_allow_html=True)

def render_loading_with_progress(tool_name: str, status_message: str, current: int = 0, total: int = 0):
    """
    Render loading with progress indicator (for multiple items)
    
    Args:
        tool_name: Name of the tool
        status_message: Status message
        current: Current item number (0 if not applicable)
        total: Total items (0 if not applicable)
    """
    # Tool icon mapping
    tool_icons = {
        "Mood Analyzer": "🤔",
        "Movie Search": "🔍",
        "Review Summarizer": "📝",
        "Preparing": "⚙️"
    }
    
    icon = tool_icons.get(tool_name, "🔄")
    
    # Build status message with progress if applicable
    full_status = status_message
    if total > 0 and current > 0:
        full_status += f" ({current}/{total})"
    
    loading_html = f"""
    <div class="loading-container">
        <div class="tool-status-badge active">
            <span class="tool-icon">{icon}</span>
            <span class="tool-name">{tool_name}</span>
            <span class="status-message">- {full_status}</span>
        </div>
        <div class="gradient-loading-bar"></div>
    </div>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)
    
    # Show progress bar if applicable
    if total > 0:
        progress = current / total if total > 0 else 0
        st.progress(progress)

