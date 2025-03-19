#!/usr/bin/env python
"""
Blueprint Filter Script for EVE Frontier Blueprint Miracle

This script filters the blueprints.json file to only include blueprints that have products
which exist in the types_filtered.json file. This ensures that the application only shows
blueprints that can be crafted with known items, eliminating 'phantom' blueprints that
appear in the UI without proper names or product information.

Usage:
    python filter_blueprints.py

Output:
    Creates a new file: data/json/blueprints_filtered.json

Notes:
    - This script should be run whenever types_filtered.json or blueprints.json is updated
    - The output file is used by the data_loader.py service in the application
    - If a blueprint has no manufacturing activity or its products aren't in types_filtered.json,
      it will be excluded from the output
"""

import json
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('filter_blueprints')

def filter_blueprints():
    """
    Filter the blueprints.json file to only include blueprints with products
    that exist in the types_filtered.json file.
    
    The function:
    1. Loads the blueprints.json and types_filtered.json files
    2. Creates a set of valid typeIDs from types_filtered.json
    3. Filters blueprints to keep only those with:
       - The blueprint ID itself exists in valid_type_ids, OR
       - At least one manufacturing product with a typeID in valid_type_ids
    4. Saves the filtered blueprints to blueprints_filtered.json
    
    Returns:
        None
    """
    # Define file paths
    data_dir = Path('data/json')
    blueprints_file = data_dir / 'blueprints.json'
    types_file = data_dir / 'types_filtered.json'
    output_file = data_dir / 'blueprints_filtered.json'
    
    logger.info(f"Loading blueprints from {blueprints_file}")
    with open(blueprints_file, 'r', encoding='utf-8') as f:
        blueprint_data = json.load(f)
    
    # Extract blueprint count and blueprints
    blueprint_count = blueprint_data.get("blueprint_count", 0)
    blueprints = blueprint_data.get("blueprints", {})
    logger.info(f"Loaded {blueprint_count} blueprints from file")
    
    logger.info(f"Loading type data from {types_file}")
    with open(types_file, 'r', encoding='utf-8') as f:
        types_data = json.load(f)
    
    # Create a set of valid typeIDs for quick lookup
    valid_type_ids = set(int(type_id) for type_id in types_data.keys())
    logger.info(f"Found {len(valid_type_ids)} valid type IDs")
    
    # Filter blueprints
    filtered_blueprints = {}
    kept_count = 0
    skipped_count = 0
    
    for blueprint_id, blueprint_info in blueprints.items():
        keep_blueprint = False
        
        # First check if the blueprint itself exists in valid_type_ids
        if int(blueprint_id) in valid_type_ids:
            keep_blueprint = True
        
        # Then check activities
        if "activities" in blueprint_info:
            activities = blueprint_info["activities"]
            
            # Check manufacturing
            if "manufacturing" in activities:
                manufacturing = activities["manufacturing"]
                if "products" in manufacturing:
                    products = manufacturing["products"]
                    for product in products:
                        if "typeID" in product and int(product["typeID"]) in valid_type_ids:
                            keep_blueprint = True
                            break
        
        if keep_blueprint:
            filtered_blueprints[blueprint_id] = blueprint_info
            kept_count += 1
        else:
            skipped_count += 1
    
    logger.info(f"Keeping {kept_count} blueprints, skipping {skipped_count} blueprints")
    
    # Create the output structure
    filtered_blueprint_data = {
        "blueprint_count": kept_count,
        "blueprints": filtered_blueprints
    }
    
    # Save filtered blueprints
    logger.info(f"Saving filtered blueprints to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_blueprint_data, f)
    
    logger.info("Filtering complete")

if __name__ == "__main__":
    filter_blueprints() 