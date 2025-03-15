#!/usr/bin/env python
"""
Test script for EVE Frontier Blueprint Miracle database models.

This script tests the initialization of database models and ensures they're properly defined.
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_models")

# Import required modules
from eve_frontier.models.base import Base, init_db, get_db
from eve_frontier.models import (
    Item, Group, Category,
    Blueprint, BlueprintProduct, BlueprintMaterial, BlueprintActivity,
    Station, MarketData, MarketOrder
)

def test_models():
    """Test database models by creating them and performing basic operations."""
    logger.info("Testing database models...")
    
    # Initialize the database (create tables)
    logger.info("Initializing database...")
    init_db()
    
    # Get a database session
    db = get_db()
    
    try:
        # Test Category model
        logger.info("Testing Category model...")
        category = Category(id=1, name="Minerals", published=True)
        db.add(category)
        db.commit()
        logger.info("Added Category: %s", category)
        
        # Test Group model
        logger.info("Testing Group model...")
        group = Group(id=1, name="Basic Minerals", category_id=1, published=True)
        db.add(group)
        db.commit()
        logger.info("Added Group: %s", group)
        
        # Test Item model
        logger.info("Testing Item model...")
        item = Item(
            id=34,
            name="Tritanium",
            group_id=1,
            base_price=5.0,
            volume=0.01,
            published=True,
            description="The most common mineral in EVE."
        )
        db.add(item)
        db.commit()
        logger.info("Added Item: %s", item)
        
        # Test Blueprint model
        logger.info("Testing Blueprint model...")
        blueprint = Blueprint(
            id=1,
            name="Tritanium Blueprint",
            max_production_limit=100
        )
        db.add(blueprint)
        db.commit()
        logger.info("Added Blueprint: %s", blueprint)
        
        # Test BlueprintActivity model
        logger.info("Testing BlueprintActivity model...")
        activity = BlueprintActivity(
            blueprint_id=1,
            activity_name="Manufacturing",
            time=300  # 5 minutes
        )
        db.add(activity)
        db.commit()
        logger.info("Added BlueprintActivity: %s", activity)
        
        # Test BlueprintProduct model
        logger.info("Testing BlueprintProduct model...")
        product = BlueprintProduct(
            blueprint_id=1,
            product_id=34,  # Tritanium
            quantity=100
        )
        db.add(product)
        db.commit()
        logger.info("Added BlueprintProduct: %s", product)
        
        # Test BlueprintMaterial model
        logger.info("Testing BlueprintMaterial model...")
        material = BlueprintMaterial(
            blueprint_id=1,
            material_id=34,  # Tritanium (just for testing)
            quantity=50
        )
        db.add(material)
        db.commit()
        logger.info("Added BlueprintMaterial: %s", material)
        
        # Test Station model
        logger.info("Testing Station model...")
        station = Station(
            id=60000004,
            name="Jita IV - Moon 4 - Caldari Navy Assembly Plant",
            region="The Forge"
        )
        db.add(station)
        db.commit()
        logger.info("Added Station: %s", station)
        
        # Test MarketData model
        logger.info("Testing MarketData model...")
        market_data = MarketData(
            item_id=34,  # Tritanium
            station_id=60000004,  # Jita
            buy_price=5.5,
            sell_price=6.0,
            buy_volume=1000000,
            sell_volume=500000
        )
        db.add(market_data)
        db.commit()
        logger.info("Added MarketData: %s", market_data)
        
        # Test MarketOrder model
        logger.info("Testing MarketOrder model...")
        market_order = MarketOrder(
            item_id=34,  # Tritanium
            station_id=60000004,  # Jita
            order_type="sell",
            price=6.0,
            volume=100000,
            min_volume=1,
            range_str="region"
        )
        db.add(market_order)
        db.commit()
        logger.info("Added MarketOrder: %s", market_order)
        
        # Test querying
        logger.info("Testing database queries...")
        
        # Query for items
        items = db.query(Item).all()
        logger.info("Found %s items", len(items))
        
        # Query for a specific item
        tritanium = db.query(Item).filter(Item.name == "Tritanium").first()
        if tritanium:
            logger.info("Found Tritanium: %s", tritanium)
        
        # Query for blueprints
        blueprints = db.query(Blueprint).all()
        logger.info("Found %s blueprints", len(blueprints))
        
        # Query for blueprint products
        products = db.query(BlueprintProduct).join(Item, BlueprintProduct.product_id == Item.id).all()
        logger.info("Found %s blueprint products", len(products))
        
        logger.info("Database models test completed successfully!")
    
    except Exception as e:
        logger.error("Error during testing: %s", e, exc_info=True)
        db.rollback()
    
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    test_models() 