"""
Script to display the mapping between TypeIDs and human-readable names.
"""

import json
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Load and display the TypeID to name mapping from types_filtered.json"""
    # Path to the types_filtered.json file
    data_path = Path("data/json/types_filtered.json")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    # Load the JSON data
    logger.info(f"Loading data from {data_path}")
    with open(data_path, 'r') as f:
        types_data = json.load(f)
    
    # Extract and display the mapping
    logger.info(f"Found {len(types_data)} items in the types_filtered.json file")
    logger.info("Sample of TypeID to Name mapping:")
    
    # Print header
    print("\n{:<10} {:<50}".format("TypeID", "Human-Readable Name"))
    print("-" * 60)
    
    # Print a subset of the mapping (first 20 items)
    for count, (type_id, item_data) in enumerate(types_data.items()):
        name = item_data.get('typeNameID', 'Unknown')
        print("{:<10} {:<50}".format(type_id, name))
        
        # Only show the first 20 mappings to avoid flooding the console
        if count >= 19:
            print("\n... and {} more items".format(len(types_data) - 20))
            break

if __name__ == "__main__":
    main() 