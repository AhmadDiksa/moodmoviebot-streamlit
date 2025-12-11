"""
Mood Analysis Tool
File: tools/mood_analyzer.py
"""

import json
import logging
from typing import Dict, Any, List, Optional
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
    
    def analyze(self, text: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Analyze mood from text with optional conversation context
        
        Args:
            text: User's text describing their mood/feelings
            conversation_history: Optional list of previous messages for context
        
        Returns:
            Dictionary with mood analysis
        """
        import time
        start_time = time.time()
        
        logger.info(f"Analyzing mood from text (length: {len(text)} chars)")
        logger.debug(f"Input text: {text[:100]}...")
        if conversation_history:
            logger.debug(f"Using conversation history - {len(conversation_history)} previous messages")
        
        try:
            # Try to get from cache first (only if no conversation history to ensure context-aware analysis)
            if not conversation_history:
                logger.debug("Checking cache for mood analysis...")
                cached = self._get_cached_analysis(text)
                if cached:
                    duration = time.time() - start_time
                    logger.info(f"Using cached mood analysis (retrieved in {duration:.3f}s)")
                    logger.debug(f"Cached result: {cached.get('detected_moods', [])}")
                    return cached
            
            # Generate prompt
            logger.debug("Building prompt for LLM...")
            prompt = self._build_prompt(text, conversation_history)
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            # Invoke LLM with conversation history
            logger.debug("Invoking LLM for mood analysis...")
            response = self.llm_manager.invoke_with_retry(
                prompt, 
                conversation_history=conversation_history
            )
            logger.debug(f"LLM response received (length: {len(response)} chars)")
            
            # Parse response
            logger.debug("Parsing LLM response...")
            result = self._parse_response(response)
            logger.debug(f"Parsed result: {result}")
            
            # Cache result (only if no conversation history)
            if not conversation_history:
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
    
    def _build_prompt(self, text: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build prompt for LLM with optional conversation context"""
        context_section = ""
        
        if conversation_history and len(conversation_history) > 0:
            # Build context from conversation history using ContextManager approach
            context_lines = []
            context_lines.append("\nKonteks percakapan sebelumnya:")
            context_lines.append("=" * 50)
            
            # Use last 5-10 messages for context
            for msg in conversation_history[-10:]:
                role = msg.get("role", "").lower()
                content = msg.get("content", "")
                
                if role == "user":
                    # Limit user message length
                    context_lines.append(f"User: {content[:300]}")
                elif role == "assistant":
                    # Extract text content (exclude movie recommendations)
                    text_content = content
                    if "**Mood Analysis:**" in text_content:
                        # Extract only mood analysis part
                        parts = text_content.split("**Recommendations:**")
                        text_content = parts[0].strip()
                    context_lines.append(f"Assistant: {text_content[:300]}")
            
            context_lines.append("=" * 50)
            context_section = "\n".join(context_lines)
            context_section += "\n\nGunakan konteks percakapan sebelumnya untuk memahami follow-up question atau perubahan mood pengguna."
        
        return f"""Analisis mood dari teks berikut dan kembalikan HANYA JSON (tanpa markdown atau komentar):

Teks pengguna saat ini: {text}
{context_section}

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
- summary: respon yang empati dan hangat dalam bahasa Indonesia, pertimbangkan konteks percakapan jika ada
- recommended_genres: 2-4 genre dari: {', '.join(GENRE_OPTIONS)}

PENTING: Kembalikan HANYA JSON tanpa markdown atau text tambahan!"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to dictionary"""
        import re
        logger.debug(f"Parsing response (length: {len(response)} chars)")
        logger.debug(f"Raw response: {response[:200]}...")
        
        try:
            # Step 1: Remove markdown code blocks if present
            cleaned = response.replace("```json", "").replace("```", "").strip()
            
            # Step 2: Remove reasoning/thinking tags (various formats)
            # Handle formats like <think>, <reasoning>, <think>, etc.
            reasoning_patterns = [
                r'<think>.*?</think>',
                r'<reasoning>.*?</reasoning>',
                r'<think>.*?</think>',
                r'<thought>.*?</thought>',
                r'<analysis>.*?</analysis>',
            ]
            for pattern in reasoning_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
            
            # Step 3: Try to extract JSON object from response
            # Find the first { and then find matching }
            json_str = None
            first_brace = cleaned.find('{')
            
            if first_brace != -1:
                # Start from first brace and find matching closing brace
                brace_count = 0
                start_pos = first_brace
                
                for i in range(start_pos, len(cleaned)):
                    if cleaned[i] == '{':
                        brace_count += 1
                    elif cleaned[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found matching closing brace
                            json_str = cleaned[start_pos:i+1]
                            break
                
                if json_str:
                    logger.debug(f"Extracted JSON from response (length: {len(json_str)} chars)")
                else:
                    logger.debug("Could not find matching closing brace, trying alternative method")
                    # Fallback: try to find JSON after reasoning tags
                    json_str = cleaned[first_brace:]
                    # Try to find the end by looking for the last }
                    last_brace = json_str.rfind('}')
                    if last_brace != -1:
                        json_str = json_str[:last_brace+1]
            else:
                # If no { found, try parsing the whole cleaned response
                json_str = cleaned
                logger.debug("No opening brace found, trying to parse entire response")
            
            # Step 4: Clean up the JSON string
            if json_str:
                json_str = json_str.strip()
                # Ensure it starts with { and ends with }
                if not json_str.startswith('{'):
                    first_brace = json_str.find('{')
                    if first_brace != -1:
                        json_str = json_str[first_brace:]
                if not json_str.endswith('}'):
                    last_brace = json_str.rfind('}')
                    if last_brace != -1:
                        json_str = json_str[:last_brace+1]
            
            logger.debug(f"Cleaned JSON string: {json_str[:200]}...")
            
            # Step 5: Parse JSON
            result = json.loads(json_str)
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
            logger.error(f"Response that failed: {response[:500]}...")
            logger.error(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            
            # Try one more time with a more aggressive extraction
            try:
                logger.debug("Attempting aggressive JSON extraction...")
                # Find the last occurrence of { that might be the start of JSON
                last_brace = response.rfind('{')
                if last_brace != -1:
                    potential_json = response[last_brace:]
                    # Find matching closing brace
                    brace_count = 0
                    end_pos = -1
                    for i, char in enumerate(potential_json):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    if end_pos != -1:
                        json_str = potential_json[:end_pos]
                        logger.debug(f"Extracted JSON using aggressive method: {json_str[:200]}...")
                        result = json.loads(json_str)
                        logger.info("Successfully parsed JSON using aggressive extraction")
                        return result
            except Exception as e2:
                logger.error(f"Aggressive extraction also failed: {e2}")
            
            raise
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis using simple pattern matching"""
        text_lower = text.lower()
        
        # Pattern matching for common moods - check most specific first
        
        # Death/grief patterns (highest priority for intensity)
        if any(word in text_lower for word in ["meninggal", "wafat", "berpulang", "tiada", "pergi", "hilang", "kehilangan", "kematian", "mati"]):
            return {
                "detected_moods": ["sedih", "sakit"],
                "intensity_score": 95,
                "emotion_type": "negative",
                "summary": "Saya turut berduka cita. Semoga Anda dan keluarga diberi kekuatan di masa sulit ini.",
                "recommended_genres": ["Drama", "Family", "Animation", "Fantasy"]
            }
        # Sickness patterns
        elif any(word in text_lower for word in ["sakit", "pusing", "demam", "flu", "batuk", "pilek"]):
            return {
                "detected_moods": ["sakit", "lelah"],
                "intensity_score": 70,
                "emotion_type": "negative",
                "summary": "Semoga lekas sembuh ya! Istirahat yang cukup dan jaga kesehatan.",
                "recommended_genres": ["Comedy", "Animation", "Family"]
            }
        # Tiredness patterns
        elif any(word in text_lower for word in ["capek", "lelah", "tired", "penat", "letih"]):
            return {
                "detected_moods": ["lelah"],
                "intensity_score": 65,
                "emotion_type": "negative",
                "summary": "Sepertinya butuh istirahat nih. Yuk santai dengan film ringan!",
                "recommended_genres": ["Comedy", "Family", "Animation"]
            }
        # Sadness patterns (broader)
        elif any(word in text_lower for word in ["sedih", "sad", "galau", "murung", "terpuruk", "down", "depresi", "putus asa"]):
            return {
                "detected_moods": ["sedih"],
                "intensity_score": 75,
                "emotion_type": "negative",
                "summary": "Ada yang mengganjal ya? Film yang tepat bisa bantu memperbaiki mood.",
                "recommended_genres": ["Comedy", "Animation", "Drama", "Family"]
            }
        # Happiness patterns
        elif any(word in text_lower for word in ["senang", "happy", "gembira", "bahagia", "joy", "excited", "semangat"]):
            return {
                "detected_moods": ["senang", "excited"],
                "intensity_score": 80,
                "emotion_type": "positive",
                "summary": "Senang banget! Mood bagus nih, cocok nonton film seru!",
                "recommended_genres": ["Adventure", "Comedy", "Action", "Animation"]
            }
        # Anger/frustration patterns
        elif any(word in text_lower for word in ["marah", "kesal", "frustrasi", "jengkel", "geram", "angry", "mad"]):
            return {
                "detected_moods": ["marah", "frustrasi"],
                "intensity_score": 70,
                "emotion_type": "negative",
                "summary": "Tenang dulu ya. Film yang menghibur bisa bantu meredakan emosi.",
                "recommended_genres": ["Comedy", "Action", "Adventure"]
            }
        # Anxiety/worry patterns
        elif any(word in text_lower for word in ["cemas", "khawatir", "anxiety", "worried", "takut", "nervous"]):
            return {
                "detected_moods": ["cemas"],
                "intensity_score": 65,
                "emotion_type": "negative",
                "summary": "Jangan terlalu khawatir. Film yang menenangkan bisa membantu.",
                "recommended_genres": ["Drama", "Family", "Animation", "Fantasy"]
            }
        # Boredom patterns
        elif any(word in text_lower for word in ["bosan", "boring", "monoton", "jenuh"]):
            return {
                "detected_moods": ["bosan"],
                "intensity_score": 55,
                "emotion_type": "neutral",
                "summary": "Wah, butuh sesuatu yang seru nih! Yuk cari film yang menarik!",
                "recommended_genres": ["Action", "Adventure", "Thriller", "Comedy"]
            }
        # Default/neutral
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