#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE Frontier Blueprint Miracle - Logger Utility

This module provides logging utilities for the application.
"""

import logging
import os
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_level=logging.INFO):
    """
    Set up a logger with the specified name and log level.
    
    Args:
        name: The name of the logger
        log_level: The log level to use
        
    Returns:
        A configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"{name}_{timestamp}.log"
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Add handlers if they don't already exist
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name):
    """
    Get a logger with the specified name.
    
    If the logger doesn't exist, it will be created with the default log level.
    
    Args:
        name: The name of the logger
        
    Returns:
        A logger instance
    """
    logger = logging.getLogger(name)
    
    # If the logger doesn't have any handlers, set it up
    if not logger.handlers:
        return setup_logger(name)
    
    return logger 