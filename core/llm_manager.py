"""
LLM Manager
File: core/llm_manager.py
"""

import streamlit as st
from typing import Optional
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class LLMManager:
    """Manage LLM operations with caching and error handling"""
    
    def __init__(self, config: AppConfig):
        """
        Initialize LLM Manager
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._llm = None
    
    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        """Lazy load LLM instance"""
        if self._llm is None:
            self._llm = self._initialize_llm()
        return self._llm
    
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize LLM with configuration"""
        logger.debug(f"Initializing LLM with model: {self.config.MODEL_NAME}")
        logger.debug(f"Temperature: {self.config.TEMPERATURE}, Max tokens: {self.config.MAX_TOKENS}")
        try:
            llm = ChatGoogleGenerativeAI(
                model=self.config.MODEL_NAME,
                google_api_key=self.config.GOOGLE_API_KEY,
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS
            )
            logger.info(f"LLM initialized successfully: {self.config.MODEL_NAME}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def invoke(
        self, 
        prompt: str, 
        system_message: Optional[str] = None
    ) -> str:
        """
        Invoke LLM with prompt
        
        Args:
            prompt: User prompt
            system_message: Optional system message
        
        Returns:
            LLM response text
        
        Raises:
            Exception: If invocation fails
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Invoking LLM - Prompt length: {len(prompt)} chars")
        if system_message:
            logger.debug(f"System message provided (length: {len(system_message)} chars)")
        
        try:
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            messages.append(HumanMessage(content=prompt))
            
            logger.debug(f"Sending {len(messages)} messages to LLM...")
            response = self.llm.invoke(messages)
            
            duration = time.time() - start_time
            response_length = len(response.content)
            logger.info(f"LLM invocation successful - Duration: {duration:.2f}s, Response length: {response_length} chars")
            logger.debug(f"Response preview: {response.content[:100]}...")
            
            return response.content.strip()
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM invocation failed after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.debug(f"Prompt that failed: {prompt[:200]}...")
            raise
    
    def invoke_with_retry(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Invoke LLM with automatic retry
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            max_retries: Maximum retry attempts
        
        Returns:
            LLM response text
        
        Raises:
            Exception: If all retries fail
        """
        import time
        overall_start = time.time()
        last_error = None
        
        logger.info(f"Invoking LLM with retry (max {max_retries} attempts)")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries}...")
                result = self.invoke(prompt, system_message)
                overall_duration = time.time() - overall_start
                logger.info(f"LLM invocation succeeded on attempt {attempt + 1} (total time: {overall_duration:.2f}s)")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"LLM attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {str(e)}")
                
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    logger.debug(f"Waiting {backoff_time}s before retry...")
                    time.sleep(backoff_time)  # Exponential backoff
        
        # All retries failed
        overall_duration = time.time() - overall_start
        logger.error(f"All {max_retries} LLM attempts failed after {overall_duration:.2f}s")
        logger.error(f"Last error: {type(last_error).__name__}: {str(last_error)}")
        raise last_error

@st.cache_resource
def get_llm_manager(config: AppConfig) -> LLMManager:
    """
    Get cached LLM Manager instance
    
    Args:
        config: Application configuration
    
    Returns:
        LLMManager instance
    """
    return LLMManager(config)