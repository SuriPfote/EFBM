#!/usr/bin/env python3

"""
Test the ProductionService's get_manufacturing_details method for Steel Plates.
"""

import logging
from eve_frontier.models.base import get_db
from eve_frontier.models import Item
from eve_frontier.services.production_service import ProductionService

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    # Get a database session
    db = get_db()
    
    # Initialize production service
    production_service = ProductionService(db)
    
    # Get Steel Plates
    steel_plates = db.query(Item).filter(Item.name == 'Steel Plates').first()
    if steel_plates:
        logger.info(f"Found Steel Plates with ID: {steel_plates.id}")
    else:
        logger.error("Steel Plates not found")
        return
    
    # Get manufacturing details
    logger.info(f"Getting manufacturing details for Steel Plates (ID: {steel_plates.id})")
    result = production_service.get_manufacturing_details(
        item_id=steel_plates.id,
        quantity=10,
        me_level=0,
        te_level=0,
        facility_bonus=0.0,
        max_depth=3
    )
    
    if result:
        logger.info(f"Manufacturing details found for Steel Plates")
        logger.info(f"Item: {result.item_name} (ID: {result.item_id})")
        logger.info(f"Blueprint: {result.blueprint_id}")
        logger.info(f"Activity: {result.activity_name} (ID: {result.activity_id})")
        logger.info(f"Time: {result.time_required}s")
        logger.info(f"Materials: {len(result.materials)}")
        
        for i, material in enumerate(result.materials):
            logger.info(f"  Material {i+1}: {material.item_name} (ID: {material.item_id}) - Quantity: {material.quantity}")
    else:
        logger.error("No manufacturing details found for Steel Plates")

if __name__ == "__main__":
    main() 