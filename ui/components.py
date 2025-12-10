"""
Reusable UI Components
File: ui/components.py
"""

import streamlit as st
from typing import Dict, Any, List
from utils.genre_utils import get_genre_emoji
from ui.styles import get_rating_stars, get_mood_emoji

def display_movie_card(movie: Dict[str, Any], index: int):
    """
    Display a movie card with all information including poster and trailer
    
    Args:
        movie: Movie dictionary
        index: Movie number in list
    """
    # Extract data
    title = movie.get('title', 'Unknown')
    year = movie.get('year', 'N/A')
    rating = movie.get('rating', 0)
    vote_count = movie.get('vote_count', 0)
    genres = movie.get('genres', [])
    overview = movie.get('overview', 'No description available')
    score = movie.get('score', 0)
    
    # Extract poster and trailer from raw_payload
    raw_payload = movie.get('raw_payload', {})
    poster_url = raw_payload.get('poster_url') or None
    trailer_url = raw_payload.get('trailer_url') or None
    
    # Clean URLs (remove None or empty strings)
    if poster_url and not isinstance(poster_url, str):
        poster_url = None
    if trailer_url and not isinstance(trailer_url, str):
        trailer_url = None
    
    # Get genre emojis
    genre_emojis = [get_genre_emoji(g) for g in genres[:3]]
    genre_text = " ".join(genre_emojis) + " " + ", ".join(genres)
    
    # Get rating stars
    stars = get_rating_stars(rating)
    
    # Create layout with columns for poster and info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display poster if available
        if poster_url:
            st.image(poster_url, use_container_width=True, caption=title)
        else:
            # Placeholder if no poster
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 10px; 
                        padding: 40px; 
                        text-align: center; 
                        color: white;">
                <p style="font-size: 2em;">🎬</p>
                <p>No Poster Available</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Create card HTML
        st.markdown(f"""
        <div class="movie-card">
            <h3>🎬 {index}. {title} ({year})</h3>
            <p><strong>⭐ Rating:</strong> {rating}/10 {stars} ({vote_count:,} votes)</p>
            <p><strong>🎭 Genre:</strong> {genre_text}</p>
            <p><strong>📊 Match Score:</strong> {score}/10</p>
            <p><strong>📝 Synopsis:</strong> {overview[:250]}{'...' if len(overview) > 250 else ''}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display trailer if available
        if trailer_url:
            video_id = None
            
            # Extract YouTube video ID from various URL formats
            if 'youtube.com/watch?v=' in trailer_url:
                video_id = trailer_url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in trailer_url:
                video_id = trailer_url.split('youtu.be/')[1].split('?')[0]
            elif 'youtube.com/embed/' in trailer_url:
                video_id = trailer_url.split('embed/')[1].split('?')[0]
            
            if video_id:
                # Embed YouTube video
                st.markdown(f"""
                <div style="margin-top: 15px;">
                    <h4>🎥 Trailer</h4>
                    <iframe width="100%" height="315" 
                            src="https://www.youtube.com/embed/{video_id}" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                    <p style="margin-top: 5px;">
                        <a href="{trailer_url}" target="_blank" style="color: #667eea; text-decoration: none;">
                            🔗 Tonton di YouTube
                        </a>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Just show link if not YouTube or unrecognized format
                st.markdown(f"""
                <div style="margin-top: 15px;">
                    <h4>🎥 Trailer</h4>
                    <p>
                        <a href="{trailer_url}" target="_blank" style="color: #667eea; text-decoration: none;">
                            🔗 Tonton Trailer
                        </a>
                    </p>
                </div>
                """, unsafe_allow_html=True)

def display_mood_analysis(mood_data: Dict[str, Any]):
    """
    Display mood analysis with visual elements
    
    Args:
        mood_data: Mood analysis dictionary
    """
    st.markdown("### 🎭 Mood Analysis")
    
    # Extract data
    moods = mood_data.get('detected_moods', [])
    intensity = mood_data.get('intensity_score', 0)
    emotion_type = mood_data.get('emotion_type', 'neutral')
    summary = mood_data.get('summary', '')
    
    # Get emoji
    emoji = get_mood_emoji(emotion_type)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mood", ", ".join(moods)[:20] + "..." if len(", ".join(moods)) > 20 else ", ".join(moods))
    
    with col2:
        st.metric("Intensity", f"{intensity}%")
        st.progress(intensity / 100)
    
    with col3:
        st.metric("Type", f"{emoji} {emotion_type.title()}")
    
    # Display summary
    st.info(f"💭 {summary}")

def display_quick_actions():
    """Display quick action buttons"""
    st.markdown("### 💡 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    actions = {
        col1: ("😊 I'm Happy!", "Lagi senang banget hari ini! Mau nonton yang seru dan menghibur."),
        col2: ("😔 I'm Sad", "Lagi sedih nih, butuh sesuatu yang menghibur tapi menyentuh."),
        col3: ("😴 I'm Tired", "Capek banget, butuh film yang ringan dan santai.")
    }
    
    for col, (label, prompt) in actions.items():
        with col:
            if st.button(label, use_container_width=True, key=f"quick_{label}"):
                return prompt
    
    return None

def display_statistics(stats: Dict[str, Any]):
    """
    Display session statistics
    
    Args:
        stats: Statistics dictionary
    """
    st.markdown("### 📊 Session Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("💬 Conversations", stats.get('conversation_count', 0))
        st.metric("🎬 Movies Recommended", stats.get('total_recommendations', 0))
    
    with col2:
        st.metric("💌 Total Messages", stats.get('total_messages', 0))
        st.metric("⏱️ Session Duration", f"{stats.get('session_duration_minutes', 0)} min")

def display_preferences_editor():
    """Display genre preferences editor"""
    st.markdown("### ⚙️ Preferences")
    
    from utils.genre_utils import get_all_genre_names
    all_genres = get_all_genre_names()
    
    # Get current preferences
    current_liked = st.session_state.get('preferred_genres', [])
    current_disliked = st.session_state.get('disliked_genres', [])
    
    # Liked genres
    liked = st.multiselect(
        "✅ Genres I Like",
        all_genres,
        default=current_liked,
        help="Select genres you enjoy watching"
    )
    
    # Disliked genres
    disliked = st.multiselect(
        "❌ Genres I Don't Like",
        all_genres,
        default=current_disliked,
        help="Select genres you prefer to avoid"
    )
    
    # Update button
    if st.button("💾 Save Preferences", use_container_width=True):
        from core.session_manager import SessionManager
        SessionManager.update_preferences(liked=liked, disliked=disliked)
        st.success("✅ Preferences saved!")
        st.rerun()

def display_sidebar_actions():
    """Display sidebar action buttons"""
    st.markdown("---")
    st.markdown("### 🎮 Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
            from core.session_manager import SessionManager
            SessionManager.clear_chat()
            st.success("Chat cleared!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Profile", use_container_width=True, key="reset_profile"):
            from core.session_manager import SessionManager
            SessionManager.reset_profile()
            st.success("Profile reset!")
            st.rerun()

def display_export_button():
    """Display export conversation button"""
    st.markdown("---")
    st.markdown("### 📥 Export")
    
    if st.button("📄 Export Conversation", use_container_width=True):
        from core.session_manager import SessionManager
        import json
        from datetime import datetime
        
        data = SessionManager.export_data()
        
        st.download_button(
            label="💾 Download JSON",
            data=json.dumps(data, indent=2, ensure_ascii=False),
            file_name=f"moodmoviebot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

def display_cache_stats():
    """Display cache statistics"""
    from utils.cache_utils import StreamlitCache
    
    stats = StreamlitCache.get_stats()
    
    with st.expander("📊 Cache Statistics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Entries", stats['total_entries'])
            st.metric("Expired Entries", stats['expired_entries'])
        
        with col2:
            st.metric("Cache Size", f"{stats['estimated_size_kb']} KB")
            
            if st.button("🗑️ Clear Cache", key="clear_cache"):
                StreamlitCache.clear_all()
                st.success("Cache cleared!")
                st.rerun()