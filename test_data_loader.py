"""
Test script for the DataLoader's load_items method.
"""

import os
import logging
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import the necessary models and services
from eve_frontier.models.item import Item, Base
from eve_frontier.services.data_loader import DataLoader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_db():
    """Set up an in-memory SQLite database for testing."""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Return a new session
    return SessionLocal()

def main():
    """Run the test for the DataLoader's load_items method."""
    # Set up the test database
    logger.info("Setting up test database")
    db = setup_test_db()
    
    # Create an instance of the DataLoader
    loader = DataLoader(db)
    
    # Path to the types_filtered.json file
    data_path = Path("data/json/types_filtered.json")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    # Load the items
    logger.info(f"Loading items from {data_path}")
    loader.load_items(str(data_path))
    
    # Query some items to verify they were loaded correctly
    items = db.query(Item).limit(10).all()
    
    logger.info("Sample items loaded:")
    for item in items:
        logger.info(f"ID: {item.id}, Name: {item.name}")
    
    # Close the database session
    db.close()

if __name__ == "__main__":
    main() 