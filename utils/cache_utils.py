"""
Cache Utilities
File: utils/cache_utils.py
"""

import streamlit as st
import hashlib
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class StreamlitCache:
    """
    Simple cache wrapper for Streamlit session state
    Better than @st.cache_data for dynamic session-based caching
    """
    
    @staticmethod
    def _get_cache_key(prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({
            "prefix": prefix,
            "args": args,
            "kwargs": kwargs
        }, sort_keys=True, default=str)
        return f"cache_{hashlib.md5(key_data.encode()).hexdigest()}"
    
    @staticmethod
    def get(prefix: str, *args, **kwargs) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            prefix: Cache namespace
            *args, **kwargs: Cache key components
        
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = StreamlitCache._get_cache_key(prefix, *args, **kwargs)
        logger.debug(f"Cache GET - Key: {cache_key[:50]}...")
        
        if cache_key in st.session_state:
            cached_data = st.session_state[cache_key]
            
            # Check if expired
            if 'expires_at' in cached_data:
                now = datetime.now()
                expires_at = cached_data['expires_at']
                if now > expires_at:
                    # Expired, remove from cache
                    del st.session_state[cache_key]
                    age = (now - cached_data.get('created_at', now)).total_seconds()
                    logger.debug(f"Cache expired: {cache_key} (age: {age:.0f}s)")
                    return None
                else:
                    remaining = (expires_at - now).total_seconds()
                    logger.debug(f"Cache hit: {cache_key} (TTL remaining: {remaining:.0f}s)")
            
            logger.debug(f"Cache hit: {cache_key}")
            return cached_data['value']
        
        logger.debug(f"Cache miss: {cache_key}")
        return None
    
    @staticmethod
    def set(
        prefix: str, 
        value: Any, 
        ttl_seconds: int = 3600,
        *args, 
        **kwargs
    ):
        """
        Set cached value
        
        Args:
            prefix: Cache namespace
            value: Value to cache
            ttl_seconds: Time to live in seconds
            *args, **kwargs: Cache key components
        """
        cache_key = StreamlitCache._get_cache_key(prefix, *args, **kwargs)
        
        try:
            value_size = len(str(value))
        except:
            value_size = 0
        
        st.session_state[cache_key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl_seconds)
        }
        
        logger.debug(f"Cache SET - Key: {cache_key[:50]}..., TTL: {ttl_seconds}s, Size: ~{value_size} chars")
    
    @staticmethod
    def clear_prefix(prefix: str):
        """Clear all cache entries with given prefix"""
        keys_to_delete = [
            key for key in st.session_state.keys() 
            if key.startswith(f"cache_") and prefix in key
        ]
        
        for key in keys_to_delete:
            del st.session_state[key]
        
        logger.info(f"Cleared {len(keys_to_delete)} cache entries with prefix: {prefix}")
    
    @staticmethod
    def clear_all():
        """Clear all cache entries"""
        cache_keys = [
            key for key in st.session_state.keys() 
            if key.startswith("cache_")
        ]
        
        for key in cache_keys:
            del st.session_state[key]
        
        logger.info(f"Cleared all cache: {len(cache_keys)} entries")
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get cache statistics"""
        cache_keys = [
            key for key in st.session_state.keys() 
            if key.startswith("cache_")
        ]
        
        total_size = 0
        expired_count = 0
        now = datetime.now()
        
        for key in cache_keys:
            cached_data = st.session_state[key]
            
            # Rough size estimation
            try:
                total_size += len(str(cached_data['value']))
            except:
                pass
            
            # Check if expired
            if 'expires_at' in cached_data:
                if now > cached_data['expires_at']:
                    expired_count += 1
        
        return {
            'total_entries': len(cache_keys),
            'expired_entries': expired_count,
            'estimated_size_bytes': total_size,
            'estimated_size_kb': round(total_size / 1024, 2)
        }

# Helper decorator for easy caching
def cache_result(ttl_seconds: int = 3600, prefix: str = "default"):
    """
    Decorator to cache function results
    
    Usage:
        @cache_result(ttl_seconds=1800, prefix="search")
        def search_movies(query):
            # expensive operation
            return results
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached = StreamlitCache.get(prefix, func.__name__, *args, **kwargs)
            if cached is not None:
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            StreamlitCache.set(
                prefix, 
                result, 
                ttl_seconds, 
                func.__name__, 
                *args, 
                **kwargs
            )
            
            return result
        
        return wrapper
    return decorator