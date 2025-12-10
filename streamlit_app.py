"""
MoodMovieBot - Main Streamlit Application
File: streamlit_app.py

Modular structure for easy debugging and maintenance
"""

import streamlit as st
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging to both console and file
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Create formatter
formatter = logging.Formatter(log_format, datefmt=date_format)

# Console handler (always show logs in terminal)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# File handler with rotation (max 10MB per file, keep 5 backups)
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)  # File gets more detailed logs
file_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Get logger for this module
logger = logging.getLogger(__name__)

# Set debug level for specific modules if needed
# logging.getLogger('core').setLevel(logging.DEBUG)
# logging.getLogger('tools').setLevel(logging.DEBUG)

# ====================== IMPORTS ======================
from config.settings import AppConfig
from core.session_manager import SessionManager
from core.llm_manager import get_llm_manager
from core.qdrant_manager import get_qdrant_manager
from tools.mood_analyzer import MoodAnalyzer
from tools.movie_search import MovieSearcher
from tools.review_summarizer import ReviewSummarizer
from ui.styles import get_custom_css
from ui.components import (
    display_movie_card,
    display_mood_analysis,
    display_quick_actions,
    display_statistics,
    display_preferences_editor,
    display_sidebar_actions,
    display_export_button,
    display_cache_stats
)

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="🎬 MoodMovieBot",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/moodmoviebot',
        'Report a bug': 'https://github.com/yourusername/moodmoviebot/issues',
        'About': """
        # 🎬 MoodMovieBot
        
        AI-powered movie recommendations based on your mood!
        
        **Features:**
        - 🎭 Smart mood analysis
        - 🎬 Personalized recommendations
        - 💾 Session memory
        - ⚡ Fast caching
        
        Made with ❤️ using Streamlit & Gemini AI
        """
    }
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ====================== INITIALIZATION ======================

def initialize_app():
    """Initialize application and check configuration"""
    logger.info("=== Initializing application ===")
    
    # Initialize session state
    logger.debug("Initializing session state...")
    SessionManager.initialize()
    logger.debug("Session state initialized")
    
    # Load configuration
    logger.debug("Loading configuration from secrets...")
    config = AppConfig.load_from_secrets()
    logger.debug(f"Configuration loaded - Model: {config.MODEL_NAME}, Collection: {config.COLLECTION_NAME}")
    
    # Check if config is valid
    if not config.is_valid():
        logger.error("Configuration validation failed - API keys missing!")
        st.error("⚠️ API keys are missing!")
        
        with st.sidebar:
            st.markdown("### 🔑 Setup Required")
            st.markdown("""
            Please add your API keys:
            
            **For Streamlit Cloud:**
            1. Go to Settings → Secrets
            2. Add:
            ```toml
            GOOGLE_API_KEY = "your_key"
            QDRANT_URL = "your_url"
            QDRANT_API_KEY = "your_key"
            ```
            
            **For Local Development:**
            1. Create `.env` file
            2. Add same keys
            
            **Get API Keys:**
            - [Gemini API](https://makersuite.google.com/app/apikey)
            - [Qdrant Cloud](https://cloud.qdrant.io/)
            """)
        
        st.stop()
    
    return config

# ====================== MAIN APP ======================

def main():
    """Main application logic"""
    
    # Initialize
    config = initialize_app()
    
    # Header
    st.title("🎬 MoodMovieBot")
    st.markdown("### 🎭 *Find the perfect movie for your mood!*")
    
    # Initialize managers (cached)
    logger.info("Initializing service managers...")
    try:
        logger.debug("Initializing LLM manager...")
        llm_manager = get_llm_manager(config)
        logger.info("LLM manager initialized successfully")
        
        logger.debug("Initializing Qdrant manager...")
        qdrant_manager = get_qdrant_manager(config)
        logger.info("Qdrant manager initialized successfully")
    except Exception as e:
        logger.exception("Failed to initialize services")
        st.error(f"❌ Failed to initialize services: {e}")
        st.info("💡 Check your API keys and try again")
        st.stop()
    
    # Initialize tools
    logger.debug("Initializing tools...")
    mood_analyzer = MoodAnalyzer(llm_manager)
    movie_searcher = MovieSearcher(qdrant_manager)
    review_summarizer = ReviewSummarizer(llm_manager)
    logger.info("All tools initialized successfully")
    
    # ====================== SIDEBAR ======================
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 Your Profile")
        
        # Statistics
        stats = SessionManager.get_statistics()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💬 Chats", stats['conversation_count'])
        with col2:
            st.metric("🎬 Movies", stats['current_recommendations'])
        
        # Current mood display
        if st.session_state.current_mood:
            st.markdown("---")
            st.markdown("### 🎭 Current Mood")
            mood = st.session_state.current_mood
            moods = mood.get('detected_moods', [])
            intensity = mood.get('intensity_score', 0)
            
            st.write(f"**Mood:** {', '.join(moods)}")
            st.progress(intensity / 100)
            st.caption(mood.get('summary', ''))
        
        # Preferences editor
        st.markdown("---")
        display_preferences_editor()
        
        # Actions
        display_sidebar_actions()
        
        # Export
        display_export_button()
        
        # Cache stats (in expander)
        st.markdown("---")
        display_cache_stats()
    
    # ====================== MAIN CONTENT ======================
    
    st.markdown("---")
    
    # Quick actions
    logger.debug("Checking quick actions...")
    quick_action_result = display_quick_actions()
    if quick_action_result:
        logger.info(f"Quick action triggered: {quick_action_result[:50]}...")
        # User clicked a quick action button
        handle_user_input(
            quick_action_result, 
            mood_analyzer, 
            movie_searcher,
            review_summarizer
        )
        st.rerun()
    
    # Display chat history
    logger.debug(f"Displaying chat history - {len(st.session_state.messages)} messages")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Display movie recommendations if available (persist cards after processing)
    if st.session_state.get('recommendations') and len(st.session_state.recommendations) > 0:
        logger.debug(f"Displaying {len(st.session_state.recommendations)} persisted movie recommendations")
        st.markdown("---")
        st.markdown("### 🎬 Recommended Movies")
        
        for idx, movie in enumerate(st.session_state.recommendations, 1):
            logger.debug(f"Displaying persisted movie {idx}/{len(st.session_state.recommendations)}: {movie.get('title', 'Unknown')}")
            # Display movie card
            display_movie_card(movie, idx)
            
            # Display review if available
            if movie.get('review_summary'):
                st.markdown(f"**💬 Netizen:** {movie.get('review_summary')}")
            
            st.markdown("---")
    
    # Chat input
    if prompt := st.chat_input("Tell me how you're feeling today..."):
        logger.info(f"User input received: {prompt[:100]}...")
        handle_user_input(prompt, mood_analyzer, movie_searcher, review_summarizer)

def handle_user_input(
    user_input: str,
    mood_analyzer: MoodAnalyzer,
    movie_searcher: MovieSearcher,
    review_summarizer: ReviewSummarizer
):
    """
    Handle user input and generate response
    
    Args:
        user_input: User's message
        mood_analyzer: Mood analyzer instance
        movie_searcher: Movie searcher instance
        review_summarizer: Review summarizer instance
    """
    import time
    start_time = time.time()
    logger.info(f"=== Processing user input (length: {len(user_input)}) ===")
    
    # Add user message
    logger.debug("Adding user message to session...")
    SessionManager.add_message("user", user_input)
    SessionManager.increment_conversation()
    logger.debug(f"Conversation count: {st.session_state.conversation_count}")
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing your mood..."):
            
            try:
                # Step 1: Analyze mood with conversation history
                logger.info("Step 1: Analyzing mood...")
                mood_start = time.time()
                
                # Get conversation history (exclude the current message we just added)
                conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
                logger.debug(f"Using {len(conversation_history)} previous messages as context")
                
                mood_result = mood_analyzer.analyze(user_input, conversation_history=conversation_history)
                mood_duration = time.time() - mood_start
                logger.info(f"Mood analysis completed in {mood_duration:.2f}s - Moods: {mood_result.get('detected_moods', [])}")
                
                SessionManager.update_mood(mood_result)
                
                # Display mood analysis
                display_mood_analysis(mood_result)
                
                # Step 2: Search movies
                st.markdown("---")
                st.markdown("### 🎬 Recommended Movies")
                
                recommended_genres = mood_result.get('recommended_genres', ['Comedy'])
                logger.info(f"Step 2: Searching movies for genres: {recommended_genres}")
                
                with st.spinner("🔍 Searching for perfect movies..."):
                    search_start = time.time()
                    movies = movie_searcher.search_by_genres(
                        recommended_genres,
                        limit=5,
                        personalize=True
                    )
                    search_duration = time.time() - search_start
                    logger.info(f"Movie search completed in {search_duration:.2f}s - Found {len(movies)} movies")
                
                if movies:
                    # Process each movie with review summary first
                    logger.debug("Processing movie reviews...")
                    processed_movies = []
                    for idx, movie in enumerate(movies, 1):
                        logger.debug(f"Processing movie {idx}/{len(movies)}: {movie.get('title', 'Unknown')}")
                        # Get review summary
                        raw_reviews = movie.get('raw_payload', {}).get('raw_reviews')
                        review_start = time.time()
                        review_summary = review_summarizer.summarize(raw_reviews)
                        review_duration = time.time() - review_start
                        logger.debug(f"Review summary generated in {review_duration:.2f}s")
                        
                        # Add review to movie dict
                        movie['review_summary'] = review_summary
                        processed_movies.append(movie)
                        
                        # Display movie card
                        display_movie_card(movie, idx)
                        
                        # Display review
                        st.markdown(f"**💬 Netizen:** {review_summary}")
                        st.markdown("---")
                    
                    # Save processed recommendations (with review summaries) to session
                    logger.debug(f"Saving {len(processed_movies)} processed recommendations to session...")
                    SessionManager.add_recommendations(processed_movies)
                    
                    response_text = f"Found {len(movies)} great movies for you! Check them out above 👆"
                    logger.info(f"Successfully displayed {len(movies)} movie recommendations")
                    
                else:
                    logger.warning("No movies found for recommended genres")
                    response_text = "Sorry, couldn't find movies matching your mood. Try being more specific!"
                
                st.success(response_text)
                
                # Add assistant message
                assistant_message = f"""**Mood Analysis:**
Detected: {', '.join(mood_result.get('detected_moods', []))}
Intensity: {mood_result.get('intensity_score', 0)}%

{mood_result.get('summary', '')}

**Recommendations:** Found {len(movies)} movies!"""
                
                SessionManager.add_message("assistant", assistant_message)
                
                total_duration = time.time() - start_time
                logger.info(f"=== User input processing completed in {total_duration:.2f}s ===")
                
            except Exception as e:
                total_duration = time.time() - start_time
                logger.exception(f"Error processing user input (duration: {total_duration:.2f}s)")
                logger.error(f"Error details: {type(e).__name__}: {str(e)}")
                st.error(f"❌ Oops! Something went wrong: {str(e)}")
                st.info("💡 Try again or check the logs")

# ====================== FOOTER ======================

def display_footer():
    """Display footer information"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: rgba(255,255,255,0.6); padding: 20px;'>
        <p>Made with ❤️ using Streamlit & Gemini AI</p>
        <p>© 2025 MoodMovieBot | <a href='#' style='color: #667eea;'>Privacy Policy</a> | <a href='#' style='color: #667eea;'>Terms of Service</a></p>
    </div>
    """, unsafe_allow_html=True)

# ====================== RUN APP ======================

if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("Starting MoodMovieBot application")
        logger.info(f"Log file: logs/app.log")
        logger.info("=" * 50)
        main()
        # display_footer()  # Optional
    except Exception as e:
        logger.exception("Critical application error")
        logger.error(f"Error type: {type(e).__name__}, Message: {str(e)}")
        st.error(f"❌ Critical Error: {e}")
        st.info("Please refresh the page or contact support")