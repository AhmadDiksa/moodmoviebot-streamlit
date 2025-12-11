"""
LLM Manager - Multi-Provider Support
File: core/llm_manager.py

Supports multiple LLM providers: Gemini, Groq, OpenAI
"""

import streamlit as st
from typing import Optional, List, Dict, Any
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class LLMManager:
    """Manage LLM operations with multi-provider support"""
    
    def __init__(self, config: AppConfig):
        """
        Initialize LLM Manager
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._llm = None
        self.provider = config.LLM_PROVIDER.lower()
    
    @property
    def llm(self) -> BaseChatModel:
        """Lazy load LLM instance"""
        if self._llm is None:
            self._llm = self._initialize_llm()
        return self._llm
    
    def _initialize_llm(self) -> BaseChatModel:
        """Initialize LLM based on provider"""
        logger.info(f"Initializing LLM - Provider: {self.provider}, Model: {self.config.MODEL_NAME}")
        logger.debug(f"Temperature: {self.config.TEMPERATURE}, Max tokens: {self.config.MAX_TOKENS}")
        
        try:
            if self.provider == "gemini":
                return self._initialize_gemini()
            elif self.provider == "groq":
                return self._initialize_groq()
            elif self.provider == "openai":
                return self._initialize_openai()
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}. Supported: gemini, groq, openai")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def _initialize_gemini(self) -> BaseChatModel:
        """Initialize Google Gemini LLM"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                model=self.config.MODEL_NAME,
                google_api_key=self.config.get_llm_api_key(),
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS
            )
            logger.info(f"Gemini LLM initialized successfully: {self.config.MODEL_NAME}")
            return llm
        except ImportError:
            raise ImportError("langchain-google-genai not installed. Install with: pip install langchain-google-genai")
    
    def _initialize_groq(self) -> BaseChatModel:
        """Initialize Groq LLM"""
        try:
            from langchain_groq import ChatGroq
            
            # Default Groq models if not specified
            model_name = self.config.MODEL_NAME if self.config.MODEL_NAME else "llama-3.1-70b-versatile"
            
            llm = ChatGroq(
                model=model_name,
                groq_api_key=self.config.get_llm_api_key(),
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS
            )
            logger.info(f"Groq LLM initialized successfully: {model_name}")
            return llm
        except ImportError:
            raise ImportError("langchain-groq not installed. Install with: pip install langchain-groq")
    
    def _initialize_openai(self) -> BaseChatModel:
        """Initialize OpenAI LLM"""
        try:
            from langchain_openai import ChatOpenAI
            
            # Default OpenAI models if not specified
            model_name = self.config.MODEL_NAME if self.config.MODEL_NAME else "gpt-3.5-turbo"
            
            llm = ChatOpenAI(
                model=model_name,
                openai_api_key=self.config.get_llm_api_key(),
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS
            )
            logger.info(f"OpenAI LLM initialized successfully: {model_name}")
            return llm
        except ImportError:
            raise ImportError("langchain-openai not installed. Install with: pip install langchain-openai")
    
    def invoke(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Invoke LLM with prompt and optional conversation history
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            conversation_history: Optional list of previous messages in format [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            LLM response text
        
        Raises:
            Exception: If invocation fails
        """
        import time
        start_time = time.time()
        
        logger.debug(f"Invoking LLM ({self.provider}) - Prompt length: {len(prompt)} chars")
        if system_message:
            logger.debug(f"System message provided (length: {len(system_message)} chars)")
        if conversation_history:
            logger.debug(f"Conversation history provided - {len(conversation_history)} previous messages")
        
        try:
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = msg.get("role", "").lower()
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))
            
            # Add current prompt
            messages.append(HumanMessage(content=prompt))
            
            logger.debug(f"Sending {len(messages)} messages to LLM (including history)...")
            response = self.llm.invoke(messages)
            
            duration = time.time() - start_time
            response_length = len(response.content)
            logger.info(f"LLM invocation successful ({self.provider}) - Duration: {duration:.2f}s, Response length: {response_length} chars")
            logger.debug(f"Response preview: {response.content[:100]}...")
            
            return response.content.strip()
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM invocation failed ({self.provider}) after {duration:.2f}s: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.debug(f"Prompt that failed: {prompt[:200]}...")
            raise
    
    def invoke_with_retry(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_retries: int = 3
    ) -> str:
        """
        Invoke LLM with automatic retry
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            conversation_history: Optional conversation history
            max_retries: Maximum retry attempts
        
        Returns:
            LLM response text
        
        Raises:
            Exception: If all retries fail
        """
        import time
        overall_start = time.time()
        last_error = None
        
        logger.info(f"Invoking LLM ({self.provider}) with retry (max {max_retries} attempts)")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries}...")
                result = self.invoke(prompt, system_message, conversation_history)
                overall_duration = time.time() - overall_start
                logger.info(f"LLM invocation succeeded ({self.provider}) on attempt {attempt + 1} (total time: {overall_duration:.2f}s)")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"LLM attempt {attempt + 1}/{max_retries} failed ({self.provider}): {type(e).__name__}: {str(e)}")
                
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    logger.debug(f"Waiting {backoff_time}s before retry...")
                    time.sleep(backoff_time)  # Exponential backoff
        
        # All retries failed
        overall_duration = time.time() - overall_start
        logger.error(f"All {max_retries} LLM attempts failed ({self.provider}) after {overall_duration:.2f}s")
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
