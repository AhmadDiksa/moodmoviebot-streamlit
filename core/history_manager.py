"""
History Manager for Chat Persistence
File: core/history_manager.py

Manages saving and loading chat history to/from local JSON file
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class HistoryManager:
    """Manage chat history persistence to local file"""
    
    HISTORY_DIR = "data"
    HISTORY_FILE = os.path.join(HISTORY_DIR, "chat_history.json")
    BACKUP_FILE = os.path.join(HISTORY_DIR, "chat_history_backup.json")
    
    @staticmethod
    def _ensure_data_dir():
        """Ensure data directory exists"""
        if not os.path.exists(HistoryManager.HISTORY_DIR):
            os.makedirs(HistoryManager.HISTORY_DIR, exist_ok=True)
            logger.debug(f"Created data directory: {HistoryManager.HISTORY_DIR}")
    
    @staticmethod
    def save_history(messages: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save chat history to JSON file
        
        Args:
            messages: List of message dictionaries
            metadata: Optional metadata dictionary
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            HistoryManager._ensure_data_dir()
            
            # Create backup if file exists
            if os.path.exists(HistoryManager.HISTORY_FILE):
                try:
                    shutil.copy2(HistoryManager.HISTORY_FILE, HistoryManager.BACKUP_FILE)
                    logger.debug("Created backup of existing history file")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            # Prepare data structure
            history_data = {
                "messages": messages,
                "metadata": metadata or {
                    "last_updated": datetime.now().isoformat(),
                    "total_messages": len(messages),
                    "version": "1.0"
                }
            }
            
            # Update metadata
            if metadata:
                history_data["metadata"].update(metadata)
            history_data["metadata"]["last_updated"] = datetime.now().isoformat()
            history_data["metadata"]["total_messages"] = len(messages)
            
            # Write to file
            with open(HistoryManager.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"History saved successfully - {len(messages)} messages")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            logger.exception("Save history error details")
            return False
    
    @staticmethod
    def load_history() -> Optional[Dict[str, Any]]:
        """
        Load chat history from JSON file
        
        Returns:
            Dictionary with messages and metadata, or None if failed
        """
        try:
            if not os.path.exists(HistoryManager.HISTORY_FILE):
                logger.debug("History file does not exist, returning None")
                return None
            
            with open(HistoryManager.HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # Validate structure
            if not isinstance(history_data, dict):
                logger.warning("Invalid history file structure: not a dictionary")
                return None
            
            if "messages" not in history_data:
                logger.warning("Invalid history file: missing 'messages' key")
                return None
            
            messages = history_data.get("messages", [])
            metadata = history_data.get("metadata", {})
            
            logger.info(f"History loaded successfully - {len(messages)} messages")
            return {
                "messages": messages,
                "metadata": metadata
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse history JSON: {e}")
            # Try to restore from backup
            if os.path.exists(HistoryManager.BACKUP_FILE):
                logger.info("Attempting to restore from backup...")
                try:
                    shutil.copy2(HistoryManager.BACKUP_FILE, HistoryManager.HISTORY_FILE)
                    return HistoryManager.load_history()
                except Exception as backup_error:
                    logger.error(f"Failed to restore from backup: {backup_error}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            logger.exception("Load history error details")
            return None
    
    @staticmethod
    def clear_history() -> bool:
        """
        Clear/delete history file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(HistoryManager.HISTORY_FILE):
                os.remove(HistoryManager.HISTORY_FILE)
                logger.info("History file deleted")
            
            if os.path.exists(HistoryManager.BACKUP_FILE):
                os.remove(HistoryManager.BACKUP_FILE)
                logger.info("History backup file deleted")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return False
    
    @staticmethod
    def append_message(message: Dict[str, Any]) -> bool:
        """
        Append a single message to history file
        
        Args:
            message: Message dictionary to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing history
            history_data = HistoryManager.load_history()
            
            if history_data is None:
                # Create new history
                messages = [message]
                metadata = {
                    "last_updated": datetime.now().isoformat(),
                    "total_messages": 1,
                    "version": "1.0"
                }
            else:
                messages = history_data.get("messages", [])
                metadata = history_data.get("metadata", {})
                messages.append(message)
            
            # Save updated history
            return HistoryManager.save_history(messages, metadata)
            
        except Exception as e:
            logger.error(f"Failed to append message: {e}")
            return False
    
    @staticmethod
    def get_history_stats() -> Dict[str, Any]:
        """
        Get statistics about saved history
        
        Returns:
            Dictionary with history statistics
        """
        try:
            history_data = HistoryManager.load_history()
            
            if history_data is None:
                return {
                    "exists": False,
                    "total_messages": 0,
                    "last_updated": None
                }
            
            messages = history_data.get("messages", [])
            metadata = history_data.get("metadata", {})
            
            return {
                "exists": True,
                "total_messages": len(messages),
                "last_updated": metadata.get("last_updated"),
                "file_size": os.path.getsize(HistoryManager.HISTORY_FILE) if os.path.exists(HistoryManager.HISTORY_FILE) else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get history stats: {e}")
            return {
                "exists": False,
                "total_messages": 0,
                "last_updated": None,
                "error": str(e)
            }

