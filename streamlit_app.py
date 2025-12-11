"""
MoodMovieBot - Main Streamlit Application
File: streamlit_app.py

Modular structure for easy debugging and maintenance
"""

import streamlit as st
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Any
import os
import hashlib

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
from ui.chat_components import (
    render_chat_message,
    render_movie_recommendation,
    render_confirmation_prompt,
    render_mood_analysis_inline,
    render_welcome_message,
    parse_confirmation_response,
    is_new_search_request,
    render_loading_with_status,
    render_loading_with_progress
)
from core.history_manager import HistoryManager
from core.context_manager import ContextManager

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

# ====================== SETUP POPUP ======================

def show_setup_popup():
    """Display popup for API key and model configuration"""
    
    # Model options for each provider
    MODEL_OPTIONS = {
        "gemini": [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-flash-latest"
        ],
        "groq": [
            "qwen/qwen3-32b",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ],
        "openai": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview"
        ]
    }
    
    # Initialize session state for setup
    if 'setup_completed' not in st.session_state:
        st.session_state.setup_completed = False
    if 'setup_provider' not in st.session_state:
        st.session_state.setup_provider = "groq"
    if 'setup_model' not in st.session_state:
        st.session_state.setup_model = MODEL_OPTIONS["groq"][0]
    if 'setup_llm_api_key' not in st.session_state:
        st.session_state.setup_llm_api_key = ""
    
    # Center the content
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main setup form in a centered container
    with st.container():
        # Add custom styling for the setup form
        st.markdown("""
        <style>
        .setup-container {
            max-width: 700px;
            margin: 0 auto;
            padding: 2rem;
            background: rgba(30, 30, 30, 0.9);
            border-radius: 15px;
            border: 2px solid #E50914;
            box-shadow: 0 10px 40px rgba(229, 9, 20, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Title
        st.markdown("## 🔑 Setup Required")
        st.markdown("Please configure your API keys to get started with MoodMovieBot!")
        st.markdown("---")
        
        # Provider selection
        provider = st.selectbox(
            "**LLM Provider**",
            options=["groq", "gemini", "openai"],
            index=["groq", "gemini", "openai"].index(st.session_state.setup_provider) if st.session_state.setup_provider in ["groq", "gemini", "openai"] else 0,
            help="Choose your preferred LLM provider"
        )
        st.session_state.setup_provider = provider
        
        # Model selection based on provider
        available_models = MODEL_OPTIONS.get(provider, MODEL_OPTIONS["groq"])
        current_model = st.session_state.setup_model if st.session_state.setup_model in available_models else available_models[0]
        model = st.selectbox(
            "**Model**",
            options=available_models,
            index=available_models.index(current_model) if current_model in available_models else 0,
            help=f"Select model for {provider}"
        )
        st.session_state.setup_model = model
        
        # API Key input
        api_key_label = {
            "gemini": "Google API Key",
            "groq": "Groq API Key",
            "openai": "OpenAI API Key"
        }.get(provider, "API Key")
        
        llm_api_key = st.text_input(
            f"**{api_key_label}**",
            value=st.session_state.setup_llm_api_key,
            type="password",
            help=f"Get your {api_key_label} from the provider's website"
        )
        st.session_state.setup_llm_api_key = llm_api_key
        
        # Help links
        with st.expander("📚 Need help getting API keys?"):
            st.markdown(f"""
            **Get API Keys:**
            - **Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)
            - **Groq**: [Groq Console](https://console.groq.com/)
            - **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys)
            
            **Note:** Qdrant configuration is loaded from `.streamlit/secrets.toml`
            """)
        
        # Save button
        if st.button("✅ Save & Continue", type="primary", use_container_width=True):
            # Validate inputs
            if not llm_api_key:
                st.error(f"⚠️ Please enter your {api_key_label}")
            else:
                # Save to session state
                st.session_state.setup_completed = True
                st.session_state.config_provider = provider
                st.session_state.config_model = model
                st.session_state.config_llm_api_key = llm_api_key
                logger.info(f"Setup completed - Provider: {provider}, Model: {model}")
                st.success("✅ Configuration saved! Loading application...")
                st.rerun()
    
    return not st.session_state.setup_completed

# ====================== INITIALIZATION ======================

def initialize_app():
    """Initialize application and check configuration"""
    logger.info("=== Initializing application ===")
    
    # Initialize session state
    logger.debug("Initializing session state...")
    SessionManager.initialize()
    logger.debug("Session state initialized")
    
    # Load history from file
    logger.debug("Loading chat history from file...")
    SessionManager.load_from_file()
    logger.debug("History loading completed")
    
    # Load configuration - check session state first, then secrets
    logger.debug("Loading configuration...")
    
    # Check if setup is completed in session state
    if st.session_state.get('setup_completed', False):
        logger.debug("Loading configuration from session state...")
        config = AppConfig()
        provider = st.session_state.get('config_provider', 'groq')
        api_key = st.session_state.get('config_llm_api_key', '')
        
        config.LLM_PROVIDER = provider
        config.MODEL_NAME = st.session_state.get('config_model', 'qwen/qwen3-32b')
        
        # Set API key based on provider
        if provider == 'gemini':
            config.GOOGLE_API_KEY = api_key
        elif provider == 'groq':
            config.GROQ_API_KEY = api_key
        elif provider == 'openai':
            config.OPENAI_API_KEY = api_key
        
        # Qdrant config is ALWAYS loaded from secrets.toml, not from session state
        try:
            secrets_config = AppConfig.load_from_secrets()
            config.QDRANT_URL = secrets_config.QDRANT_URL
            config.QDRANT_API_KEY = secrets_config.QDRANT_API_KEY
            logger.debug("Qdrant configuration loaded from secrets.toml")
        except Exception as e:
            logger.warning(f"Failed to load Qdrant config from secrets: {e}")
            # Try direct access to secrets
            try:
                config.QDRANT_URL = st.secrets.get("QDRANT_URL", "")
                config.QDRANT_API_KEY = st.secrets.get("QDRANT_API_KEY", "")
            except:
                # Fallback to environment variables
                import os
                config.QDRANT_URL = os.getenv("QDRANT_URL", "")
                config.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        
        logger.debug(f"Configuration loaded from session - Provider: {config.LLM_PROVIDER}, Model: {config.MODEL_NAME}")
    else:
        # Try loading from secrets
        logger.debug("Loading configuration from secrets...")
        config = AppConfig.load_from_secrets()
        logger.debug(f"Configuration loaded from secrets - Provider: {config.LLM_PROVIDER}, Model: {config.MODEL_NAME}")
    
    # Check if config is valid
    if not config.is_valid():
        logger.warning("Configuration validation failed - API keys missing!")
        # Show setup popup
        if show_setup_popup():
            st.stop()
        else:
            # Reload config from session state after setup
            config = AppConfig()
            provider = st.session_state.get('config_provider', 'groq')
            api_key = st.session_state.get('config_llm_api_key', '')
            
            config.LLM_PROVIDER = provider
            config.MODEL_NAME = st.session_state.get('config_model', 'qwen/qwen3-32b')
            
            # Set API key based on provider
            if provider == 'gemini':
                config.GOOGLE_API_KEY = api_key
            elif provider == 'groq':
                config.GROQ_API_KEY = api_key
            elif provider == 'openai':
                config.OPENAI_API_KEY = api_key
            
            # Qdrant config is ALWAYS loaded from secrets.toml, not from session state
            try:
                secrets_config = AppConfig.load_from_secrets()
                config.QDRANT_URL = secrets_config.QDRANT_URL
                config.QDRANT_API_KEY = secrets_config.QDRANT_API_KEY
                logger.debug("Qdrant configuration loaded from secrets.toml")
            except Exception as e:
                logger.warning(f"Failed to load Qdrant config from secrets: {e}")
                # Try direct access to secrets
                try:
                    config.QDRANT_URL = st.secrets.get("QDRANT_URL", "")
                    config.QDRANT_API_KEY = st.secrets.get("QDRANT_API_KEY", "")
                except:
                    # Fallback to environment variables
                    import os
                    config.QDRANT_URL = os.getenv("QDRANT_URL", "")
                    config.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    
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
    
    # ====================== HANDLE CONFIRMATION RESPONSE ======================
    # Handle confirmation response FIRST (before rendering UI)
    # This ensures movie search is called immediately when user clicks "yes"
    if 'confirmation_response' in st.session_state:
        response = st.session_state.confirmation_response
        del st.session_state.confirmation_response
        
        if response == "yes":
            # User approved, proceed with movie search
            pending = SessionManager.get_pending_confirmation()
            if pending:
                logger.info("User approved recommendation, proceeding with movie search")
                handle_movie_search(
                    pending.get('genres', []),
                    pending.get('mood_result', {}),
                    mood_analyzer,
                    movie_searcher,
                    review_summarizer
                )
                SessionManager.clear_pending_confirmation()
                st.rerun()
        elif response == "no":
            # User rejected
            SessionManager.add_message("assistant", "Baik, tidak masalah. Jika Anda ingin melihat rekomendasi film nanti, silakan beri tahu saya!")
            SessionManager.clear_pending_confirmation()
            st.rerun()
        elif response == "change":
            # User wants to change
            SessionManager.add_message("assistant", "Baik, genre apa yang ingin Anda tonton? Silakan sebutkan genre atau mood yang Anda inginkan.")
            SessionManager.clear_pending_confirmation()
            st.rerun()
    
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
    
    # Full-width chat interface
    # Display welcome message if no messages
    if len(st.session_state.messages) == 0:
        render_welcome_message()
    
    # Display chat history using chat components
    logger.debug(f"Displaying chat history - {len(st.session_state.messages)} messages")
    for message in st.session_state.messages:
        render_chat_message(message, show_timestamp=False)
    
    # Chat input
    if prompt := st.chat_input("Ceritakan bagaimana perasaan Anda hari ini..."):
        logger.info(f"User input received: {prompt[:100]}...")
        handle_user_input(prompt, mood_analyzer, movie_searcher, review_summarizer)

def handle_user_input(
    user_input: str,
    mood_analyzer: MoodAnalyzer,
    movie_searcher: MovieSearcher,
    review_summarizer: ReviewSummarizer
):
    """
    Handle user input and generate response with confirmation flow
    
    Args:
        user_input: User's message
        mood_analyzer: Mood analyzer instance
        movie_searcher: Movie searcher instance
        review_summarizer: Review summarizer instance
    """
    import time
    start_time = time.time()
    logger.info(f"=== Processing user input (length: {len(user_input)}) ===")
    
    # Check if user is requesting a new search (not responding to confirmation)
    # This must be checked BEFORE checking pending_confirmation to avoid false positives
    is_new_search = is_new_search_request(user_input)
    if is_new_search:
        # Clear any pending confirmation and proceed with new mood analysis
        SessionManager.clear_pending_confirmation()
        logger.info("User requesting new search, cleared pending confirmation")
        # Continue with normal flow (mood analysis) - skip confirmation check below
    
    # Check if user is responding to confirmation (only if not a new search request)
    pending_confirmation = SessionManager.get_pending_confirmation()
    if pending_confirmation and not is_new_search:
        # User is responding to confirmation prompt
        logger.info("User responding to confirmation prompt")
        confirmation_response = parse_confirmation_response(user_input)
        
        if confirmation_response == "yes":
            # User approved, proceed with movie search
            logger.info("User approved recommendation, proceeding with movie search")
            SessionManager.add_message("user", user_input)
            SessionManager.increment_conversation()
            
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                handle_movie_search(
                    pending_confirmation.get('genres', []),
                    pending_confirmation.get('mood_result', {}),
                    mood_analyzer,
                    movie_searcher,
                    review_summarizer
                )
            
            SessionManager.clear_pending_confirmation()
            return
        
        elif confirmation_response == "no":
            # User rejected
            SessionManager.add_message("user", user_input)
            SessionManager.increment_conversation()
            
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                st.markdown("Baik, tidak masalah. Jika Anda ingin melihat rekomendasi film nanti, silakan beri tahu saya!")
                SessionManager.add_message("assistant", "Baik, tidak masalah. Jika Anda ingin melihat rekomendasi film nanti, silakan beri tahu saya!")
            
            SessionManager.clear_pending_confirmation()
            return
        
        elif confirmation_response == "change":
            # User wants to change genre
            SessionManager.add_message("user", user_input)
            SessionManager.increment_conversation()
            
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                st.markdown("Baik, saya akan menganalisis ulang berdasarkan permintaan Anda.")
                SessionManager.add_message("assistant", "Baik, saya akan menganalisis ulang berdasarkan permintaan Anda.")
            
            SessionManager.clear_pending_confirmation()
            # Continue with normal flow to re-analyze
    
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
        try:
            # Step 1: Analyze mood with conversation history using ContextManager
            logger.info("Step 1: Analyzing mood...")
            
            # Show loading status for mood analysis
            render_loading_with_status(
                tool_name="Mood Analyzer",
                status_message="Menganalisis mood Anda...",
                show_spinner=True
            )
            
            mood_start = time.time()
            
            # Build context using ContextManager
            conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
            logger.debug(f"Using {len(conversation_history)} previous messages as context")
            
            mood_result = mood_analyzer.analyze(user_input, conversation_history=conversation_history)
            mood_duration = time.time() - mood_start
            logger.info(f"Mood analysis completed in {mood_duration:.2f}s - Moods: {mood_result.get('detected_moods', [])}")
            
            # Store user_input in mood_result for semantic search
            mood_result['user_input'] = user_input
            
            SessionManager.update_mood(mood_result)
            
            # Clear loading and display mood analysis inline
            st.empty()  # Clear loading indicator
            render_mood_analysis_inline(mood_result)
            
            # Step 2: Ask for confirmation before searching movies
            recommended_genres = mood_result.get('recommended_genres', ['Comedy'])
            mood_summary = mood_result.get('summary', '')
            
            logger.info(f"Step 2: Asking for confirmation for genres: {recommended_genres}")
            
            # Show preparing status
            render_loading_with_status(
                tool_name="Preparing",
                status_message="Mempersiapkan rekomendasi...",
                show_spinner=False
            )
            
            # Small delay for visual feedback
            import time
            time.sleep(0.3)
            
            # Store pending confirmation
            SessionManager.set_pending_confirmation({
                'genres': recommended_genres,
                'mood_result': mood_result
            })
            
            # Clear loading and display confirmation prompt
            st.empty()  # Clear loading indicator
            render_confirmation_prompt(recommended_genres, mood_summary)
            
            # Add assistant message with confirmation
            confirmation_message = f"""**Analisis Mood:**
Mood terdeteksi: {', '.join(mood_result.get('detected_moods', []))}
Intensitas: {mood_result.get('intensity_score', 0)}%

{mood_summary}

Berdasarkan mood Anda, saya bisa merekomendasikan film dengan genre: {', '.join(recommended_genres)}. Apakah Anda ingin melihat rekomendasi film?"""
            
            SessionManager.add_message("assistant", confirmation_message, metadata={
                "type": "confirmation",
                "genres": recommended_genres,
                "mood_result": mood_result
            })
            
            total_duration = time.time() - start_time
            logger.info(f"=== User input processing completed in {total_duration:.2f}s ===")
            
        except Exception as e:
                total_duration = time.time() - start_time
                logger.exception(f"Error processing user input (duration: {total_duration:.2f}s)")
                logger.error(f"Error details: {type(e).__name__}: {str(e)}")
                st.error(f"❌ Oops! Terjadi kesalahan: {str(e)}")
                st.info("💡 Coba lagi atau periksa log")
                SessionManager.add_message("assistant", f"Maaf, terjadi kesalahan: {str(e)}")

def handle_movie_search(
    recommended_genres: List[str],
    mood_result: Dict[str, Any],
    mood_analyzer: MoodAnalyzer,
    movie_searcher: MovieSearcher,
    review_summarizer: ReviewSummarizer
):
    """
    Handle movie search and display recommendations
    
    IMPORTANT: This function ONLY uses MovieSearcher which searches Qdrant database.
    No external APIs (TMDB, OMDB, etc.) are used. No fallback mechanism.
    
    Args:
        recommended_genres: List of genre names
        mood_result: Mood analysis result
        mood_analyzer: Mood analyzer instance
        movie_searcher: Movie searcher instance (ONLY uses Qdrant)
        review_summarizer: Review summarizer instance
    """
    import time
    import hashlib
    
    # Validate that movie_searcher is available
    if movie_searcher is None:
        logger.error("MovieSearcher is None - cannot search movies. Movie search ONLY uses Qdrant.")
        st.error("❌ Error: Movie search service tidak tersedia. Pastikan Qdrant database terhubung.")
        SessionManager.clear_pending_confirmation()  # Clear pending confirmation on error
        return
    
    logger.info(f"Searching movies from Qdrant ONLY for genres: {recommended_genres}")
    logger.debug("IMPORTANT: Movie search uses ONLY Qdrant database. No external APIs.")
    
    # Show loading status for movie search
    render_loading_with_status(
        tool_name="Movie Search",
        status_message="Mencari film yang cocok untuk Anda...",
        show_spinner=True
    )
    
    # Create context hash from mood for cache uniqueness
    context_string = f"{mood_result.get('detected_moods', [])}-{mood_result.get('intensity_score', 0)}-{recommended_genres}"
    context_hash = hashlib.md5(context_string.encode()).hexdigest()[:12]
    logger.debug(f"Context hash for search: {context_hash}")
    
    # Generate query text for semantic search
    # Format: user input + mood summary + genres
    user_input = mood_result.get('user_input', '')
    mood_summary = mood_result.get('summary', '')
    genres_text = ', '.join(recommended_genres)
    
    query_text = None
    if user_input or mood_summary:
        query_parts = []
        if user_input:
            query_parts.append(user_input)
        if mood_summary:
            query_parts.append(f"Mood: {mood_summary}")
        if genres_text:
            query_parts.append(f"Looking for: {genres_text}")
        query_text = ". ".join(query_parts)
        logger.debug(f"Generated query text for semantic search: {query_text[:100]}...")
    
    search_start = time.time()
    # Search ONLY from Qdrant - no fallback to other sources
    # Uses hybrid search (semantic + filter) if query_text is provided
    movies = movie_searcher.search_by_genres(
        recommended_genres,
        limit=5,
        personalize=True,
        context_hash=context_hash,
        query_text=query_text
    )
    search_duration = time.time() - search_start
    logger.info(f"Movie search from Qdrant completed in {search_duration:.2f}s - Found {len(movies)} movies")
    
    if not movies:
        logger.warning("No movies found from Qdrant database. No fallback to external APIs.")
        st.info("Maaf, saya tidak menemukan film yang sesuai di database. Silakan coba dengan genre lain atau pastikan Qdrant database terhubung dengan baik.")
        SessionManager.add_message("assistant", "Maaf, saya tidak menemukan film yang sesuai di database. Silakan coba dengan genre lain.")
        SessionManager.clear_pending_confirmation()  # Clear pending confirmation when no movies found
        return
    
    if movies:
        # Clear movie search loading
        st.empty()  # Clear loading indicator
        
        # IMPORTANT: Validate that all movies have raw_payload from Qdrant before processing
        logger.debug("Validating movies from Qdrant before processing...")
        valid_movies = []
        invalid_count = 0
        
        for movie in movies:
            # Validate movie has raw_payload (proof it comes from Qdrant)
            if not movie.get('raw_payload'):
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' missing raw_payload from Qdrant. Filtering out.")
                invalid_count += 1
                continue
            
            # Validate movie has required fields
            if not movie.get('title'):
                logger.warning(f"Movie missing title field. Filtering out.")
                invalid_count += 1
                continue
            
            # Validate raw_payload is a dict (from Qdrant)
            raw_payload = movie.get('raw_payload')
            if not isinstance(raw_payload, dict):
                logger.warning(f"Movie '{movie.get('title', 'Unknown')}' has invalid raw_payload type: {type(raw_payload)}. Filtering out.")
                invalid_count += 1
                continue
            
            valid_movies.append(movie)
        
        if invalid_count > 0:
            logger.warning(f"Filtered out {invalid_count} invalid movies. Only {len(valid_movies)} valid movies from Qdrant will be processed.")
        
        if not valid_movies:
            logger.error("No valid movies from Qdrant to display. All movies were filtered out.")
            st.error("❌ Error: Tidak ada film valid dari database Qdrant. Semua film tidak memiliki data yang valid.")
            SessionManager.add_message("assistant", "Maaf, tidak ada film valid yang ditemukan di database Qdrant.")
            SessionManager.clear_pending_confirmation()  # Clear pending confirmation when no valid movies
            return
        
        # Process each movie with review summary
        logger.debug(f"Processing {len(valid_movies)} valid movies from Qdrant...")
        processed_movies = []
        
        for idx, movie in enumerate(valid_movies, 1):
            logger.debug(f"Processing movie {idx}/{len(valid_movies)} from Qdrant: {movie.get('title', 'Unknown')}")
            
            # Validate again before processing
            if not movie.get('raw_payload'):
                logger.error(f"Movie '{movie.get('title', 'Unknown')}' lost raw_payload during processing. Skipping.")
                continue
            
            # Show loading status for review summarization
            render_loading_with_progress(
                tool_name="Review Summarizer",
                status_message="Meringkas review netizen",
                current=idx,
                total=len(valid_movies)
            )
            
            # Get review summary from raw_payload (from Qdrant)
            raw_reviews = movie.get('raw_payload', {}).get('raw_reviews')
            if raw_reviews:
                review_start = time.time()
                review_summary = review_summarizer.summarize(raw_reviews)
                review_duration = time.time() - review_start
                logger.debug(f"Review summary generated in {review_duration:.2f}s")
                movie['review_summary'] = review_summary
            else:
                movie['review_summary'] = "Belum ada review dari netizen"
            
            # Final validation before adding to processed list
            if movie.get('raw_payload'):
                processed_movies.append(movie)
            else:
                logger.error(f"Movie '{movie.get('title', 'Unknown')}' missing raw_payload after processing. Skipping.")
            
            # Clear loading indicator after each movie
            if idx < len(movies):
                st.empty()  # Clear loading indicator
        
        # Clear final loading indicator
        st.empty()
        
        # Final validation before displaying: Ensure all movies have raw_payload from Qdrant
        if not processed_movies:
            logger.error("No valid movies from Qdrant to display after processing.")
            st.error("❌ Error: Tidak ada film valid dari database Qdrant setelah diproses.")
            SessionManager.add_message("assistant", "Maaf, tidak ada film valid yang dapat ditampilkan.")
            SessionManager.clear_pending_confirmation()  # Clear pending confirmation when no processed movies
            return
        
        # Validate all movies have raw_payload one more time before display
        final_valid_movies = [m for m in processed_movies if m.get('raw_payload')]
        if len(final_valid_movies) < len(processed_movies):
            logger.warning(f"Filtered out {len(processed_movies) - len(final_valid_movies)} movies without raw_payload before display.")
            processed_movies = final_valid_movies
        
        if not processed_movies:
            logger.error("No valid movies from Qdrant to display after final validation.")
            st.error("❌ Error: Tidak ada film valid dari database Qdrant setelah validasi akhir.")
            SessionManager.add_message("assistant", "Maaf, tidak ada film valid yang dapat ditampilkan.")
            SessionManager.clear_pending_confirmation()  # Clear pending confirmation when no final valid movies
            return
        
        # Display movies using chat components (all from Qdrant)
        logger.info(f"Displaying {len(processed_movies)} valid movies from Qdrant database")
        render_movie_recommendation(processed_movies)
        
        # Save processed recommendations to session (all validated from Qdrant)
        logger.debug(f"Saving {len(processed_movies)} validated recommendations from Qdrant to session...")
        SessionManager.add_recommendations(processed_movies)
        
        # Add assistant message with recommendations (all from Qdrant)
        response_text = f"Saya menemukan {len(processed_movies)} film yang cocok untuk Anda dari database Qdrant! 🎬"
        st.success(response_text)
        
        SessionManager.add_message("assistant", response_text, metadata={
            "type": "recommendation",
            "movies": processed_movies,  # All validated from Qdrant
            "genres": recommended_genres
        })
        
        # Clear pending confirmation after successful recommendation display
        SessionManager.clear_pending_confirmation()
        logger.debug("Cleared pending confirmation after successful movie recommendation")
        
        logger.info(f"Successfully displayed {len(processed_movies)} movie recommendations (all from Qdrant database)")
    
    else:
        # This should not be reached due to check above, but kept for safety
        logger.warning("No movies found from Qdrant for recommended genres. No fallback to external APIs.")
        response_text = "Maaf, saya tidak menemukan film yang sesuai di database Qdrant. Silakan coba dengan genre lain atau pastikan database terhubung dengan baik."
        st.info(response_text)
        
        SessionManager.add_message("assistant", response_text)
        SessionManager.clear_pending_confirmation()  # Clear pending confirmation in safety case

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