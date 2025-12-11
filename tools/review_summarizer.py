"""
Review Summarization Tool
File: tools/review_summarizer.py
"""

import logging
import re
from typing import Any, List
from core.llm_manager import LLMManager
from utils.cache_utils import StreamlitCache

logger = logging.getLogger(__name__)

class ReviewSummarizer:
    """Summarize movie reviews into catchy one-liners"""
    
    def __init__(self, llm_manager: LLMManager):
        """
        Initialize Review Summarizer
        
        Args:
            llm_manager: LLM Manager instance
        """
        self.llm_manager = llm_manager
    
    def summarize(self, raw_reviews: Any) -> str:
        """
        Summarize reviews into one catchy Indonesian sentence
        
        Args:
            raw_reviews: Reviews in any format (list, string, JSON, etc.)
        
        Returns:
            Catchy one-sentence summary
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Summarizing reviews - Type: {type(raw_reviews).__name__}")
        
        try:
            # Check cache first
            cache_key = str(raw_reviews)[:100] if raw_reviews else "empty"
            logger.debug(f"Checking cache with key: {cache_key[:50]}...")
            cached = StreamlitCache.get("review_summary", cache_key)
            if cached:
                duration = time.time() - start_time
                logger.info(f"Using cached review summary (retrieved in {duration:.3f}s)")
                return cached
            
            # Normalize reviews to list of strings
            logger.debug("Normalizing reviews...")
            reviews = self._normalize_reviews(raw_reviews)
            logger.debug(f"Normalized to {len(reviews)} review(s)")
            
            if not reviews:
                logger.warning("No reviews to summarize")
                return "Belum ada ulasan."
            
            # Generate summary using LLM
            logger.debug("Generating summary using LLM...")
            summary = self._generate_summary(reviews)
            logger.debug(f"Generated summary: {summary[:100]}...")
            
            # Cache result
            StreamlitCache.set("review_summary", summary, 7200, cache_key)  # 2 hours TTL
            
            duration = time.time() - start_time
            logger.info(f"Review summarized successfully in {duration:.2f}s (length: {len(summary)} chars)")
            return summary
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Review summarization failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.warning("Returning fallback summary")
            return "Netizen bilang filmnya bagus!"
    
    def _normalize_reviews(self, raw_reviews: Any) -> List[str]:
        """
        Normalize reviews to list of strings
        
        Args:
            raw_reviews: Reviews in any format
        
        Returns:
            List of review strings
        """
        logger.debug(f"Normalizing reviews - Input type: {type(raw_reviews).__name__}")
        reviews = []
        
        # Handle None or empty
        if not raw_reviews:
            logger.debug("Raw reviews is None or empty")
            return []
        
        # Handle list
        if isinstance(raw_reviews, list):
            logger.debug(f"Processing list with {len(raw_reviews)} items")
            for item in raw_reviews:
                if item and str(item).strip():
                    reviews.append(str(item).strip())
            logger.debug(f"Extracted {len(reviews)} reviews from list")
        
        # Handle string
        elif isinstance(raw_reviews, str):
            text = raw_reviews.strip()
            logger.debug(f"Processing string (length: {len(text)} chars)")
            
            # Check if empty or null
            if not text or text.lower() == "null":
                logger.debug("String is empty or 'null'")
                return []
            
            # Try to parse as JSON
            try:
                import json
                parsed = json.loads(text)
                logger.debug("Successfully parsed as JSON")
                if isinstance(parsed, list):
                    reviews = [str(x).strip() for x in parsed if str(x).strip()]
                    logger.debug(f"Extracted {len(reviews)} reviews from JSON list")
                else:
                    reviews = [text]
                    logger.debug("JSON is not a list, using as single review")
            except:
                logger.debug("Not valid JSON, trying delimiter splitting")
                # Split by common delimiters
                if "|||" in text:
                    reviews = [r.strip() for r in text.split("|||") if r.strip()]
                    logger.debug(f"Split by ||| - {len(reviews)} reviews")
                elif any(sep in text for sep in ["\n", ";", "|"]):
                    reviews = [r.strip() for r in re.split(r'[;\n|]', text) if r.strip()]
                    logger.debug(f"Split by delimiters - {len(reviews)} reviews")
                else:
                    reviews = [text] if len(text) > 10 else []
                    logger.debug(f"Using as single review: {len(reviews)}")
        
        # Limit to first 6 reviews
        result = reviews[:6]
        logger.debug(f"Final normalized reviews count: {len(result)} (limited from {len(reviews)})")
        return result
    
    def _generate_summary(self, reviews: List[str]) -> str:
        """
        Generate catchy summary using LLM
        
        Args:
            reviews: List of review strings
        
        Returns:
            One-sentence summary
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Generating summary from {len(reviews)} reviews")
        
        try:
            # Prepare reviews for prompt (truncate long ones)
            review_snippets = [
                r[:150] + "..." if len(r) > 150 else r 
                for r in reviews
            ]
            logger.debug(f"Prepared {len(review_snippets)} review snippets for prompt")
            
            prompt = f"""Jadikan semua ulasan ini jadi SATU KALIMAT gaul ala netizen Indonesia (maksimal 25 kata):

{chr(10).join([f"- {r}" for r in review_snippets])}

Contoh style yang diinginkan:
- "Katanya masterpiece banget, bikin nangis bombay!"
- "Netizen bilang best movie ever, acting on point!"
- "Ceritanya mind-blowing, wajib nonton berkali-kali!"

PENTING: Tulis HANYA satu kalimat tanpa kutip atau markdown!"""

            logger.debug(f"Invoking LLM with prompt (length: {len(prompt)} chars)")
            response = self.llm_manager.invoke(prompt)
            logger.debug(f"LLM response received (length: {len(response)} chars)")
            
            # Clean response - extract only the actual summary text
            summary = response.strip()
            original_summary = summary
            
            # Remove reasoning/thinking tags if present
            reasoning_patterns = [
                r'<think>.*?</think>',
                r'<reasoning>.*?</reasoning>',
                r'<think>.*?</think>',
                r'<thought>.*?</thought>',
            ]
            for pattern in reasoning_patterns:
                summary = re.sub(pattern, '', summary, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove markdown code blocks
            summary = summary.replace("```", "").strip()
            
            # Remove quotes
            summary = re.sub(r'^["\']+|[,"\']+$', '', summary)
            
            # If response is too long, try to extract just the first sentence or first 150 chars
            if len(summary) > 200:
                logger.debug(f"Summary too long ({len(summary)} chars), extracting first sentence...")
                # Try to find first sentence (ending with . ! or ?)
                sentence_match = re.search(r'^[^.!?]+[.!?]', summary)
                if sentence_match:
                    summary = sentence_match.group(0).strip()
                    logger.debug(f"Extracted first sentence: {summary[:100]}...")
                else:
                    # If no sentence ending found, try to find first line break or take first 150 chars
                    first_line = summary.split('\n')[0].strip()
                    if len(first_line) > 0 and len(first_line) <= 200:
                        summary = first_line
                        logger.debug(f"Took first line: {summary[:100]}...")
                    else:
                        # If still too long, take first 150 chars
                        summary = summary[:150].strip()
                        logger.debug(f"Took first 150 chars: {summary[:100]}...")
            
            if summary != original_summary:
                logger.debug(f"Cleaned summary (removed quotes/markdown/reasoning)")
            
            # Final cleanup: remove any remaining reasoning keywords at the start
            reasoning_keywords = ['okay', 'let', 'tackle', 'user', 'wants', 'reviews', 'combine']
            first_words = summary.lower().split()[:3]
            if any(keyword in first_words for keyword in reasoning_keywords):
                # Try to find actual summary after reasoning text
                # Look for sentence that doesn't start with reasoning keywords
                sentences = re.split(r'[.!?]+', summary)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 20:
                        first_words_sent = sentence.lower().split()[:3]
                        if not any(keyword in first_words_sent for keyword in reasoning_keywords):
                            summary = sentence
                            logger.debug(f"Extracted actual summary after reasoning: {summary[:100]}...")
                            break
            
            # Validate length - be more lenient (up to 200 chars is OK)
            if summary and len(summary) <= 200 and len(summary) > 10:
                duration = time.time() - start_time
                logger.debug(f"Summary generated successfully in {duration:.2f}s (length: {len(summary)} chars)")
                return summary
            else:
                logger.warning(f"Summary still invalid (length: {len(summary) if summary else 0} chars), using fallback")
                return self._fallback_summary(reviews)
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM summary generation failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.warning("Falling back to heuristic summary")
            return self._fallback_summary(reviews)
    
    def _fallback_summary(self, reviews: List[str]) -> str:
        """
        Fallback summary using simple heuristics
        
        Args:
            reviews: List of review strings
        
        Returns:
            Simple summary
        """
        # Count positive/negative keywords
        positive_words = ["good", "great", "amazing", "excellent", "love", "best", 
                         "bagus", "keren", "mantap", "seru", "recommended"]
        negative_words = ["bad", "poor", "boring", "waste", "disappointing",
                         "jelek", "buruk", "mengecewakan", "membosankan"]
        
        text_combined = " ".join(reviews).lower()
        
        positive_count = sum(1 for word in positive_words if word in text_combined)
        negative_count = sum(1 for word in negative_words if word in text_combined)
        
        if positive_count > negative_count:
            return "Netizen bilang filmnya bagus banget!"
        elif negative_count > positive_count:
            return "Netizen ada yang kurang suka sih..."
        else:
            return "Netizen pendapatnya beragam tentang film ini."