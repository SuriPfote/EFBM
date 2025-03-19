#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Blueprint Browser tab.
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_blueprint_browser")

# Add the current directory to the path so we can import the application modules
sys.path.append(os.getcwd())

try:
    # Import the application modules
    from eve_frontier.models.base import get_db
    from eve_frontier.models import Blueprint
    from eve_frontier.services.search_service import SearchService
    
    # Get a database session
    db = get_db()
    
    try:
        # Create a search service
        search_service = SearchService(db)
        
        # Test searching for blueprints
        query = "steel"
        logger.info(f"Searching for blueprints matching '{query}'...")
        
        blueprints = search_service.search_blueprints(
            query=query,
            activity_name=None,
            limit=10
        )
        
        logger.info(f"Found {len(blueprints)} blueprints matching '{query}'")
        
        # Print the results
        for blueprint in blueprints:
            logger.info(f"  ID: {blueprint.id}, Name: {blueprint.name}")
    
    except Exception as e:
        logger.error(f"Error searching for blueprints: {e}")
    
    finally:
        db.close()

except ImportError as e:
    logger.error(f"Error importing modules: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}") 