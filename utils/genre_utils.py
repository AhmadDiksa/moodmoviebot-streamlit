"""
Genre Utilities
File: utils/genre_utils.py
"""

from typing import List, Tuple
from functools import lru_cache

# TMDB Genre ID Mapping
GENRE_MAP = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science fiction": 878,
    "sci-fi": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37
}

# Reverse mapping (ID to name)
GENRE_ID_TO_NAME = {v: k for k, v in GENRE_MAP.items()}

@lru_cache(maxsize=128)
def genre_names_to_ids(names: Tuple[str, ...]) -> List[int]:
    """
    Convert genre names to IDs
    
    Args:
        names: Tuple of genre names (tuple for caching)
    
    Returns:
        List of genre IDs
    
    Example:
        >>> genre_names_to_ids(("Action", "Comedy"))
        [28, 35]
    """
    return [
        GENRE_MAP.get(name.lower()) 
        for name in names 
        if GENRE_MAP.get(name.lower())
    ]

@lru_cache(maxsize=128)
def genre_ids_to_names(ids: Tuple[int, ...]) -> List[str]:
    """
    Convert genre IDs to names
    
    Args:
        ids: Tuple of genre IDs (tuple for caching)
    
    Returns:
        List of genre names (capitalized)
    
    Example:
        >>> genre_ids_to_names((28, 35))
        ['Action', 'Comedy']
    """
    return [
        GENRE_ID_TO_NAME.get(id, "unknown").title() 
        for id in ids
    ]

def get_all_genre_names() -> List[str]:
    """Get all available genre names"""
    return sorted([name.title() for name in set(GENRE_MAP.keys())])

def get_genre_id(name: str) -> int:
    """
    Get genre ID from name
    
    Args:
        name: Genre name
    
    Returns:
        Genre ID or None if not found
    """
    return GENRE_MAP.get(name.lower())

def is_valid_genre(name: str) -> bool:
    """Check if genre name is valid"""
    return name.lower() in GENRE_MAP

def get_genre_emoji(name: str) -> str:
    """Get emoji for genre"""
    emoji_map = {
        "action": "💥",
        "adventure": "🗺️",
        "animation": "🎨",
        "comedy": "😂",
        "crime": "🔫",
        "documentary": "📹",
        "drama": "🎭",
        "family": "👨‍👩‍👧‍👦",
        "fantasy": "🧙",
        "history": "📜",
        "horror": "👻",
        "music": "🎵",
        "mystery": "🔍",
        "romance": "❤️",
        "science fiction": "🚀",
        "sci-fi": "🚀",
        "thriller": "😱",
        "war": "⚔️",
        "western": "🤠"
    }
    return emoji_map.get(name.lower(), "🎬")