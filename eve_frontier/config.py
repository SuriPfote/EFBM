"""
Configuration module for EVE Frontier Blueprint Miracle.

This module defines configuration settings for the application using Pydantic.
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator


class AppConfig(BaseModel):
    """Application configuration settings."""
    
    # Application metadata
    app_name: str = "EVE Frontier Blueprint Miracle"
    app_version: str = "1.0.0"
    
    # Directory paths
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")
    
    # Data file paths
    json_dir: Path = Path("data/json")
    market_logs_dir: Path = Path("data/csv/Marketlogs")
    refined_market_data_dir: Path = Path("data/refined_market_data")
    
    # Database settings
    db_url: str = "sqlite:///eve_frontier.db"
    
    # UI settings
    theme: str = "default"
    font_size: int = 10
    window_width: int = 1200
    window_height: int = 800
    
    @field_validator('json_dir', 'market_logs_dir', 'refined_market_data_dir', 'data_dir', 'logs_dir')
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        """Validate that the directory exists or create it."""
        v.mkdir(parents=True, exist_ok=True)
        return v


# Create the default configuration
config = AppConfig() 