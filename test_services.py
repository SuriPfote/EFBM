#!/usr/bin/env python
"""
Test script for EVE Frontier Blueprint Miracle services.

This script tests the functionality of the implemented services.
"""

import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_services")

# Import required modules
from eve_frontier.models.base import init_db, get_db
from eve_frontier.models import Category, Group, Item
from eve_frontier.services import (
    DataLoader,
    SearchService,
    ProductionService,
    MarketService,
    UserPreferencesService
)

def test_data_loader(db):
    """Test the DataLoader service."""
    logger.info("Testing DataLoader service...")
    
    # Initialize the DataLoader
    data_loader = DataLoader(db)
    
    # Check methods
    logger.info("DataLoader methods: %s", dir(data_loader))
    
    # Check if categories already exist
    category_count = db.query(Category).count()
    if category_count > 0:
        logger.info("Categories already exist in database (%s categories found)", category_count)
    else:
        # Try loading some data if JSON files exist
        json_dir = Path("data/json")
        categories_file = json_dir / "categories.json"
        
        if categories_file.exists():
            logger.info("Loading categories from %s", categories_file)
            try:
                count = data_loader.load_categories(categories_file)
                logger.info("Loaded %s categories", count)
            except Exception as e:
                logger.warning("Error loading categories: %s", e)
        else:
            logger.warning("Categories file not found at %s", categories_file)
    
    logger.info("DataLoader service test completed")

def test_search_service(db):
    """Test the SearchService."""
    logger.info("Testing SearchService...")
    
    # Initialize the SearchService
    search_service = SearchService(db)
    
    # Check methods
    logger.info("SearchService methods: %s", dir(search_service))
    
    # Try searching for items
    query = "tritanium"
    logger.info("Searching for items with query: %s", query)
    items = search_service.search_items(query)
    logger.info("Found %s items", len(items))
    
    # Try getting categories
    logger.info("Getting categories")
    categories = search_service.get_categories()
    logger.info("Found %s categories", len(categories))
    
    logger.info("SearchService test completed")

def test_production_service(db):
    """Test the ProductionService."""
    logger.info("Testing ProductionService...")
    
    # Initialize the ProductionService
    production_service = ProductionService(db)
    
    # Check methods
    logger.info("ProductionService methods: %s", dir(production_service))
    
    # Try getting manufacturing details for an item
    # Check if we have any items in the database
    item = db.query(Item).first()
    if item:
        item_id = item.id
        logger.info("Getting manufacturing details for item ID: %s (%s)", item_id, item.name)
        details = production_service.get_manufacturing_details(item_id)
        
        if details:
            logger.info("Manufacturing details: %s", details.to_dict())
        else:
            logger.warning("No manufacturing details found for item ID: %s", item_id)
    else:
        logger.warning("No items found in database, skipping manufacturing details test")
    
    logger.info("ProductionService test completed")

def test_market_service(db):
    """Test the MarketService."""
    logger.info("Testing MarketService...")
    
    # Initialize the MarketService
    market_service = MarketService(db)
    
    # Check methods
    logger.info("MarketService methods: %s", dir(market_service))
    
    # Try getting market data for an item if any items exist
    item = db.query(Item).first()
    if item:
        item_id = item.id
        logger.info("Getting market data for item ID: %s (%s)", item_id, item.name)
        market_data = market_service.get_market_data(item_id)
        logger.info("Found %s market data entries", len(market_data))
        
        # Try getting market statistics
        logger.info("Getting market statistics for item ID: %s", item_id)
        stats = market_service.get_market_statistics(item_id)
        if stats:
            logger.info("Market statistics: %s", stats)
    else:
        logger.warning("No items found in database, skipping market data test")
    
    logger.info("MarketService test completed")

def test_user_preferences_service():
    """Test the UserPreferencesService."""
    logger.info("Testing UserPreferencesService...")
    
    # Initialize the UserPreferencesService with a test directory
    test_config_dir = Path("test_config")
    preferences_service = UserPreferencesService(str(test_config_dir))
    
    # Check methods
    logger.info("UserPreferencesService methods: %s", dir(preferences_service))
    
    # Try getting and setting preferences
    theme = preferences_service.get_preference("general", "theme")
    logger.info("Current theme: %s", theme)
    
    logger.info("Setting theme to 'dark'")
    preferences_service.set_preference("general", "theme", "dark")
    
    theme = preferences_service.get_preference("general", "theme")
    logger.info("Updated theme: %s", theme)
    
    # Try adding a recent search
    logger.info("Adding recent search")
    preferences_service.add_recent_search("tritanium")
    
    recent_searches = preferences_service.get_preference("ui", "recent_searches")
    logger.info("Recent searches: %s", recent_searches)
    
    # Reset preferences
    logger.info("Resetting preferences")
    preferences_service.reset_preferences()
    
    logger.info("UserPreferencesService test completed")
    
    # Clean up test directory
    if test_config_dir.exists():
        prefs_file = test_config_dir / "preferences.json"
        if prefs_file.exists():
            prefs_file.unlink()
        test_config_dir.rmdir()

def main():
    """Main function to run all tests."""
    logger.info("Starting service tests...")
    
    # Initialize the database
    logger.info("Initializing database...")
    init_db()
    
    # Get a database session
    db = get_db()
    
    try:
        # Test each service
        test_data_loader(db)
        test_search_service(db)
        test_production_service(db)
        test_market_service(db)
        test_user_preferences_service()
        
        logger.info("All service tests completed successfully!")
    
    except Exception as e:
        logger.error("Error during testing: %s", e, exc_info=True)
    
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    main() 