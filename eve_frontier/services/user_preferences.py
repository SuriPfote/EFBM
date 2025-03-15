"""
User Preferences Service for EVE Frontier Blueprint Miracle.

This module provides functionality to store and retrieve user preferences and settings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """Service for managing user preferences and settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the UserPreferencesService.
        
        Args:
            config_dir: Optional custom directory for storing configuration files.
                If not provided, will use a default location in the user's home directory.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to a directory in the user's home
            self.config_dir = Path.home() / ".eve_frontier"
        
        # Ensure the directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to the preferences file
        self.preferences_file = self.config_dir / "preferences.json"
        
        # Initialize preferences dictionary
        self._preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """
        Load preferences from the preferences file.
        
        Returns:
            Dictionary containing the preferences
        """
        if not self.preferences_file.exists():
            logger.info(f"Preferences file not found at {self.preferences_file}, creating default")
            return self._create_default_preferences()
        
        try:
            with open(self.preferences_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Error parsing preferences file at {self.preferences_file}, using defaults")
            return self._create_default_preferences()
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
            return self._create_default_preferences()
    
    def _save_preferences(self) -> bool:
        """
        Save the current preferences to the preferences file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self._preferences, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            return False
    
    def _create_default_preferences(self) -> Dict[str, Any]:
        """
        Create default preferences.
        
        Returns:
            Dictionary containing default preferences
        """
        return {
            "general": {
                "theme": "system",  # "light", "dark", or "system"
                "language": "en",
                "auto_check_updates": True,
            },
            "market": {
                "default_region_id": 10000002,  # The Forge
                "default_trading_hub_id": 30000142,  # Jita
                "default_price_source": "sell_min",  # "sell_min", "buy_max", "average"
                "price_history_days": 7,
            },
            "production": {
                "default_me_level": 0,
                "default_te_level": 0,
                "default_facility_type": "station",  # "station", "engineering_complex", "refinery"
                "default_facility_bonus": 0.0,
                "ignore_item_categories": [9],  # Blueprints
            },
            "ui": {
                "font_size": "medium",  # "small", "medium", "large"
                "show_tooltips": True,
                "search_include_results_count": 50,
                "recent_searches": [],
                "favorite_items": [],
                "favorite_blueprints": [],
            },
            "data": {
                "sde_auto_update": True,
                "market_data_auto_update": True,
                "market_data_update_interval_hours": 1,
            },
        }
    
    def get_preference(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a preference value.
        
        Args:
            section: Preference section
            key: Preference key
            default: Default value to return if the preference doesn't exist
            
        Returns:
            Preference value or default
        """
        try:
            return self._preferences.get(section, {}).get(key, default)
        except Exception as e:
            logger.error(f"Error getting preference {section}.{key}: {e}")
            return default
    
    def set_preference(self, section: str, key: str, value: Any) -> bool:
        """
        Set a preference value.
        
        Args:
            section: Preference section
            key: Preference key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the section exists
            if section not in self._preferences:
                self._preferences[section] = {}
            
            # Set the value
            self._preferences[section][key] = value
            
            # Save the preferences
            return self._save_preferences()
        except Exception as e:
            logger.error(f"Error setting preference {section}.{key}: {e}")
            return False
    
    def get_all_preferences(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all preferences.
        
        Returns:
            Dictionary containing all preferences
        """
        return self._preferences.copy()
    
    def reset_preferences(self, section: Optional[str] = None) -> bool:
        """
        Reset preferences to default values.
        
        Args:
            section: Optional section to reset. If None, reset all preferences.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            defaults = self._create_default_preferences()
            
            if section is None:
                # Reset all preferences
                self._preferences = defaults
            elif section in defaults:
                # Reset only the specified section
                self._preferences[section] = defaults[section]
            else:
                logger.warning(f"Unknown preference section: {section}")
                return False
            
            # Save the preferences
            return self._save_preferences()
        except Exception as e:
            logger.error(f"Error resetting preferences: {e}")
            return False
    
    def add_recent_search(self, search_term: str, max_recent_searches: int = 10) -> bool:
        """
        Add a search term to the recent searches list.
        
        Args:
            search_term: Search term to add
            max_recent_searches: Maximum number of recent searches to keep
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current list of recent searches
            recent_searches = self.get_preference("ui", "recent_searches", [])
            
            # Remove the search term if it already exists (to move it to the top)
            if search_term in recent_searches:
                recent_searches.remove(search_term)
            
            # Add the search term to the beginning of the list
            recent_searches.insert(0, search_term)
            
            # Trim the list if it's too long
            if len(recent_searches) > max_recent_searches:
                recent_searches = recent_searches[:max_recent_searches]
            
            # Update the preference
            return self.set_preference("ui", "recent_searches", recent_searches)
        except Exception as e:
            logger.error(f"Error adding recent search: {e}")
            return False
    
    def add_favorite_item(self, item_id: int) -> bool:
        """
        Add an item to the favorite items list.
        
        Args:
            item_id: ID of the item to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current list of favorite items
            favorite_items = self.get_preference("ui", "favorite_items", [])
            
            # Only add if it's not already in the list
            if item_id not in favorite_items:
                favorite_items.append(item_id)
                # Update the preference
                return self.set_preference("ui", "favorite_items", favorite_items)
            
            return True
        except Exception as e:
            logger.error(f"Error adding favorite item: {e}")
            return False
    
    def remove_favorite_item(self, item_id: int) -> bool:
        """
        Remove an item from the favorite items list.
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current list of favorite items
            favorite_items = self.get_preference("ui", "favorite_items", [])
            
            # Remove the item if it exists
            if item_id in favorite_items:
                favorite_items.remove(item_id)
                # Update the preference
                return self.set_preference("ui", "favorite_items", favorite_items)
            
            return True
        except Exception as e:
            logger.error(f"Error removing favorite item: {e}")
            return False 