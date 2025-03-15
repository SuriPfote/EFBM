#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE Frontier Blueprint Miracle - Launcher

This script serves as the launcher for the EVE Frontier Blueprint Miracle application.
It imports and executes the main function from the eve_frontier.main module.
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging for the launcher
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "launcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("launcher")

if __name__ == "__main__":
    logger.info("Launching EVE Frontier Blueprint Miracle")
    
    try:
        # Import the main function from the eve_frontier package
        from eve_frontier.main import main
        
        # Execute the main function
        sys.exit(main())
    except ImportError as e:
        logger.error(f"Failed to import main function: {e}")
        print(f"Error: Could not start application - {e}")
        print("Make sure the eve_frontier package is installed correctly.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: Unexpected error - {e}")
        sys.exit(1) 