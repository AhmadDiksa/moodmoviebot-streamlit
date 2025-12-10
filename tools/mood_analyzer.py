"""
Mood Analysis Tool
File: tools/mood_analyzer.py
"""

import json
import logging
from typing import Dict, Any
from core.llm_manager import LLMManager
from utils.cache_utils import cache_result
from config.settings import MOOD_OPTIONS, GENRE_OPTIONS

logger = logging.getLogger(__name__)

class MoodAnalyzer:
    """Analyze user's mood from text"""
    
    def __init__(self, llm_manager: LLMManager):
        """
        Initialize Mood Analyzer
        
        Args:
            llm_manager: LLM Manager instance
        """
        self.llm_manager = llm_manager
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze mood from text
        
        Args:
            text: User's text describing their mood/feelings
        
        Returns:
            Dictionary with mood analysis
        """
        import time
        start_time = time.time()
        
        logger.info(f"Analyzing mood from text (length: {len(text)} chars)")
        logger.debug(f"Input text: {text[:100]}...")
        
        try:
            # Try to get from cache first
            logger.debug("Checking cache for mood analysis...")
            cached = self._get_cached_analysis(text)
            if cached:
                duration = time.time() - start_time
                logger.info(f"Using cached mood analysis (retrieved in {duration:.3f}s)")
                logger.debug(f"Cached result: {cached.get('detected_moods', [])}")
                return cached
            
            # Generate prompt
            logger.debug("Building prompt for LLM...")
            prompt = self._build_prompt(text)
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            # Invoke LLM
            logger.debug("Invoking LLM for mood analysis...")
            response = self.llm_manager.invoke_with_retry(prompt)
            logger.debug(f"LLM response received (length: {len(response)} chars)")
            
            # Parse response
            logger.debug("Parsing LLM response...")
            result = self._parse_response(response)
            logger.debug(f"Parsed result: {result}")
            
            # Cache result
            logger.debug("Caching analysis result...")
            self._cache_analysis(text, result)
            
            duration = time.time() - start_time
            moods = result.get('detected_moods', [])
            intensity = result.get('intensity_score', 0)
            logger.info(f"Mood analyzed in {duration:.2f}s - Moods: {moods}, Intensity: {intensity}%")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Mood analysis failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.warning("Falling back to pattern-based analysis")
            fallback_result = self._fallback_analysis(text)
            logger.info(f"Fallback analysis result: {fallback_result.get('detected_moods', [])}")
            return fallback_result
    
    def _build_prompt(self, text: str) -> str:
        """Build prompt for LLM"""
        return f"""Analisis mood dari teks berikut dan kembalikan HANYA JSON (tanpa markdown atau komentar):

Teks pengguna: {text}

Format JSON yang harus dikembalikan:
{{
    "detected_moods": ["mood1", "mood2"],
    "intensity_score": 0-100,
    "emotion_type": "positive/neutral/negative",
    "summary": "ringkasan empati 1-2 kalimat dalam bahasa Indonesia",
    "recommended_genres": ["Genre1", "Genre2", "Genre3"]
}}

Panduan:
- detected_moods: pilih 1-3 mood dari: {', '.join(MOOD_OPTIONS)}
- intensity_score: 0 (sangat ringan) sampai 100 (sangat kuat)
- emotion_type: pilih salah satu: positive, neutral, atau negative
- summary: respon yang empati dan hangat dalam bahasa Indonesia
- recommended_genres: 2-4 genre dari: {', '.join(GENRE_OPTIONS)}

PENTING: Kembalikan HANYA JSON tanpa markdown atau text tambahan!"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to dictionary"""
        logger.debug(f"Parsing response (length: {len(response)} chars)")
        logger.debug(f"Raw response: {response[:200]}...")
        
        try:
            # Clean markdown if present
            cleaned = response.replace("```json", "").replace("```", "").strip()
            logger.debug(f"Cleaned response: {cleaned[:200]}...")
            
            # Parse JSON
            result = json.loads(cleaned)
            logger.debug(f"JSON parsed successfully: {list(result.keys())}")
            
            # Validate required fields
            required_fields = [
                'detected_moods', 
                'intensity_score', 
                'emotion_type',
                'summary',
                'recommended_genres'
            ]
            
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                logger.error(f"Available fields: {list(result.keys())}")
                raise ValueError(f"Missing required field(s): {missing_fields}")
            
            # Clamp intensity score
            original_intensity = result.get('intensity_score', 0)
            result['intensity_score'] = max(0, min(100, result['intensity_score']))
            if original_intensity != result['intensity_score']:
                logger.debug(f"Intensity score clamped from {original_intensity} to {result['intensity_score']}")
            
            logger.debug(f"Validation passed - Moods: {result.get('detected_moods')}, Intensity: {result.get('intensity_score')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response that failed: {response}")
            logger.error(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            raise
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis using simple pattern matching"""
        text_lower = text.lower()
        
        # Pattern matching for common moods
        if any(word in text_lower for word in ["sakit", "pusing", "demam", "flu"]):
            return {
                "detected_moods": ["sakit", "lelah"],
                "intensity_score": 70,
                "emotion_type": "negative",
                "summary": "Semoga lekas sembuh ya! Istirahat yang cukup dan jaga kesehatan.",
                "recommended_genres": ["Comedy", "Animation", "Family"]
            }
        elif any(word in text_lower for word in ["capek", "lelah", "tired"]):
            return {
                "detected_moods": ["lelah"],
                "intensity_score": 65,
                "emotion_type": "negative",
                "summary": "Sepertinya butuh istirahat nih. Yuk santai dengan film ringan!",
                "recommended_genres": ["Comedy", "Family", "Animation"]
            }
        elif any(word in text_lower for word in ["senang", "happy", "gembira"]):
            return {
                "detected_moods": ["senang"],
                "intensity_score": 80,
                "emotion_type": "positive",
                "summary": "Senang banget! Mood bagus nih, cocok nonton film seru!",
                "recommended_genres": ["Adventure", "Comedy", "Action"]
            }
        elif any(word in text_lower for word in ["sedih", "sad", "galau"]):
            return {
                "detected_moods": ["sedih"],
                "intensity_score": 60,
                "emotion_type": "negative",
                "summary": "Ada yang mengganjal ya? Film yang tepat bisa bantu memperbaiki mood.",
                "recommended_genres": ["Comedy", "Animation", "Drama"]
            }
        else:
            return {
                "detected_moods": ["netral"],
                "intensity_score": 50,
                "emotion_type": "neutral",
                "summary": "Baik, saya siap membantu menemukan film yang cocok untukmu!",
                "recommended_genres": ["Comedy", "Drama", "Adventure"]
            }
    
    def _get_cached_analysis(self, text: str) -> Dict[str, Any]:
        """Get cached mood analysis"""
        from utils.cache_utils import StreamlitCache
        return StreamlitCache.get("mood_analysis", text)
    
    def _cache_analysis(self, text: str, result: Dict[str, Any]):
        """Cache mood analysis result"""
        from utils.cache_utils import StreamlitCache
        StreamlitCache.set("mood_analysis", result, 1800, text)  # 30 minutes TTL