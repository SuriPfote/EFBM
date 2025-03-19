#!/usr/bin/env python
"""
Database Initialization Script for EVE Frontier Blueprint Miracle.

This script initializes the database and loads sample data for testing.
"""

import logging
import sys
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("init_database")

# Import required modules
from eve_frontier.models.base import init_db, get_db, Base, engine
from eve_frontier.models import (
    Category, Group, Item, Blueprint, 
    BlueprintProduct, BlueprintMaterial, BlueprintActivity
)
from eve_frontier.services.data_loader import DataLoader

def table_is_empty(db, model):
    """Check if a table is empty."""
    try:
        count = db.query(model).count()
        return count == 0
    except Exception:
        # If an error occurs, assume the table is empty or doesn't exist
        return True

def create_sample_blueprints(db):
    """Create sample blueprints for testing if none exist."""
    logger.info("Creating sample blueprints for testing...")
    
    # Check if there are any blueprints
    if not table_is_empty(db, Blueprint):
        logger.info("Blueprints already exist, skipping...")
        return
    
    # Create a sample blueprint
    blueprint = Blueprint(
        id=1,
        name="Steel Plates Blueprint",
        max_production_limit=10
    )
    db.add(blueprint)
    
    # Add a manufacturing activity
    activity = BlueprintActivity(
        blueprint_id=1,
        activity_name="Manufacturing",
        time=300  # 5 minutes
    )
    db.add(activity)
    
    # Add materials
    materials = [
        BlueprintMaterial(blueprint_id=1, material_id=84182, quantity=10),  # Steel
        BlueprintMaterial(blueprint_id=1, material_id=84206, quantity=2)    # Steel Beams
    ]
    db.add_all(materials)
    
    # Add products
    products = [
        BlueprintProduct(blueprint_id=1, product_id=84204, quantity=5)  # Steel Plates
    ]
    db.add_all(products)
    
    # Create another sample blueprint
    blueprint2 = Blueprint(
        id=2,
        name="Shield Generator Blueprint",
        max_production_limit=5
    )
    db.add(blueprint2)
    
    # Add a manufacturing activity
    activity2 = BlueprintActivity(
        blueprint_id=2,
        activity_name="Manufacturing",
        time=600  # 10 minutes
    )
    db.add(activity2)
    
    # Add materials
    materials2 = [
        BlueprintMaterial(blueprint_id=2, material_id=84712, quantity=3),  # Shield Generator Parts
        BlueprintMaterial(blueprint_id=2, material_id=84204, quantity=2)   # Steel Plates
    ]
    db.add_all(materials2)
    
    # Add products
    products2 = [
        BlueprintProduct(blueprint_id=2, product_id=82652, quantity=1)  # Shield Generator
    ]
    db.add_all(products2)
    
    # Commit changes
    db.commit()
    logger.info("Sample blueprints created successfully")

def main():
    """Initialize the database and load sample data."""
    logger.info("Initializing database...")
    
    # Force recreate all tables
    logger.info("Dropping all tables and recreating them...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # Get database session
    db = get_db()
    
    try:
        # Create a data loader
        loader = DataLoader(db)
        
        # Define data directory
        data_dir = Path("data/json")
        
        # Load categories if needed
        categories_file = data_dir / "categories.json"
        if categories_file.exists():
            logger.info(f"Loading categories from {categories_file}")
            count = loader.load_categories(categories_file)
            logger.info(f"Loaded {count} categories")
        else:
            logger.warning(f"Categories file not found: {categories_file}")
        
        # Load groups if needed
        groups_file = data_dir / "groups.json"
        if groups_file.exists():
            logger.info(f"Loading groups from {groups_file}")
            count = loader.load_groups(groups_file)
            logger.info(f"Loaded {count} groups")
        else:
            logger.warning(f"Groups file not found: {groups_file}")
        
        # Load items if needed
        items_file = data_dir / "types_filtered.json"
        if items_file.exists():
            logger.info(f"Loading items from {items_file}")
            count = loader.load_items(items_file)
            logger.info(f"Loaded {count} items")
        else:
            logger.warning(f"Items file not found: {items_file}")
        
        # Load blueprints from filtered file if it exists, otherwise fall back to original
        blueprints_file = data_dir / "blueprints_filtered.json"
        if not blueprints_file.exists():
            logger.warning(f"Filtered blueprints file not found: {blueprints_file}")
            logger.info("Falling back to original blueprints.json")
            blueprints_file = data_dir / "blueprints.json"
        
        if blueprints_file.exists():
            logger.info(f"Loading blueprints from {blueprints_file}")
            count = loader.load_blueprints(blueprints_file)
            logger.info(f"Loaded {count} blueprints")
        else:
            logger.warning(f"Blueprints file not found: {blueprints_file}")
            # Create sample blueprints for testing
            create_sample_blueprints(db)
        
        logger.info("Database initialization complete!")
    
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}", exc_info=True)
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    main() 