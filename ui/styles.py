"""
UI Styles and CSS
File: ui/styles.py
"""

def get_custom_css() -> str:
    """
    Get custom CSS for Streamlit app
    
    Returns:
        CSS string
    """
    return """
    <style>
        /* ===== Main Theme ===== */
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* ===== Chat Messages ===== */
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            backdrop-filter: blur(10px);
        }
        
        /* ===== Sidebar ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(0, 0, 0, 0.3) 0%, rgba(0, 0, 0, 0.1) 100%);
            backdrop-filter: blur(10px);
        }
        
        /* ===== Buttons ===== */
        .stButton>button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .stButton>button:hover {
            background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .stButton>button:active {
            transform: translateY(0px);
        }
        
        /* ===== Movie Cards ===== */
        .movie-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .movie-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 255, 255, 0.4);
        }
        
        .movie-card h3 {
            color: #ffffff;
            font-size: 1.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .movie-card p {
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.6;
            margin: 8px 0;
        }
        
        .movie-card strong {
            color: #ffffff;
            font-weight: 600;
        }
        
        /* ===== Movie Poster ===== */
        .stImage img {
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }
        
        .stImage img:hover {
            transform: scale(1.05);
        }
        
        /* ===== YouTube Embed ===== */
        iframe {
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        /* ===== Metric Cards ===== */
        .metric-card {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        /* ===== Headers ===== */
        h1, h2, h3, h4, h5, h6 {
            color: white !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        /* ===== Status Indicators ===== */
        .status-healthy {
            color: #10b981;
            font-weight: bold;
        }
        
        .status-warning {
            color: #f59e0b;
            font-weight: bold;
        }
        
        .status-error {
            color: #ef4444;
            font-weight: bold;
        }
        
        /* ===== Input Fields ===== */
        .stTextInput>div>div>input {
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
        }
        
        /* ===== Multiselect ===== */
        .stMultiSelect>div>div {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        
        /* ===== Expander ===== */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: white !important;
        }
        
        /* ===== Progress Bar ===== */
        .stProgress>div>div>div>div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        /* ===== Tabs ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: white;
            padding: 10px 20px;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        /* ===== Animations ===== */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .movie-card, .metric-card {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* ===== Scrollbar ===== */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
        }
        
        /* ===== Loading Spinner ===== */
        .stSpinner>div {
            border-top-color: #667eea !important;
        }
        
        /* ===== Tooltips ===== */
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: rgba(0, 0, 0, 0.8);
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 8px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        
        /* ===== Footer ===== */
        footer {
            visibility: hidden;
        }
        
        /* ===== Success/Error Messages ===== */
        .stSuccess, .stError, .stWarning, .stInfo {
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
    </style>
    """

def get_mood_emoji(emotion_type: str) -> str:
    """
    Get emoji for emotion type
    
    Args:
        emotion_type: positive/neutral/negative
    
    Returns:
        Emoji string
    """
    emoji_map = {
        "positive": "😊",
        "neutral": "😐",
        "negative": "😔"
    }
    return emoji_map.get(emotion_type, "😐")

def get_rating_stars(rating: float) -> str:
    """
    Convert rating to star emoji
    
    Args:
        rating: Rating from 0-10
    
    Returns:
        Star emoji string
    """
    if rating >= 8:
        return "⭐⭐⭐⭐⭐"
    elif rating >= 7:
        return "⭐⭐⭐⭐"
    elif rating >= 6:
        return "⭐⭐⭐"
    elif rating >= 5:
        return "⭐⭐"
    else:
        return "⭐"