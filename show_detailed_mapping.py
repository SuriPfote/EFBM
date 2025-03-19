"""
Enhanced script to display detailed mapping between TypeIDs and human-readable names.
"""

import json
from pathlib import Path
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Load and display detailed TypeID to name mapping from types_filtered.json"""
    # Paths to necessary data files
    types_path = Path("data/json/types_filtered.json")
    groups_path = Path("data/json/groups.json")
    
    if not types_path.exists():
        logger.error(f"Types data file not found: {types_path}")
        return
    
    if not groups_path.exists():
        logger.error(f"Groups data file not found: {groups_path}")
        return
    
    # Load the JSON data
    logger.info(f"Loading types data from {types_path}")
    with open(types_path, 'r') as f:
        types_data = json.load(f)
    
    logger.info(f"Loading groups data from {groups_path}")
    try:
        with open(groups_path, 'r') as f:
            groups_data = json.load(f)
    except:
        logger.warning("Could not load groups data. Will continue without group information.")
        groups_data = {}
    
    # Group mapping
    group_names = {}
    for group_id, group_data in groups_data.items():
        group_names[int(group_id)] = group_data.get('groupNameID', f'Group {group_id}')
    
    # Organize items by group
    items_by_group = defaultdict(list)
    for type_id, item_data in types_data.items():
        group_id = item_data.get('groupID', 0)
        items_by_group[group_id].append((int(type_id), item_data))
    
    # Display statistics
    logger.info(f"Found {len(types_data)} items across {len(items_by_group)} groups")
    
    # Print a sample from each group (up to 5 items per group)
    print("\n=== MAPPING BETWEEN TYPEIDS AND HUMAN-READABLE NAMES ===\n")
    
    for group_id, items in items_by_group.items():
        group_name = group_names.get(group_id, f"Group {group_id}")
        print(f"\n== GROUP: {group_name} (ID: {group_id}) - {len(items)} items ==")
        print("{:<10} {:<50} {:<15} {:<10}".format("TypeID", "Name", "Base Price", "Volume"))
        print("-" * 85)
        
        # Sort items by ID
        items.sort(key=lambda x: x[0])
        
        # Show up to 5 items from each group
        for i, (type_id, item_data) in enumerate(items):
            if i >= 5:
                print(f"... and {len(items) - 5} more items in this group")
                break
                
            name = item_data.get('typeNameID', 'Unknown')
            base_price = item_data.get('basePrice', 0)
            volume = item_data.get('volume', 0)
            
            # Format base price with commas for readability
            price_str = f"{base_price:,.2f}" if base_price else "N/A"
            
            print("{:<10} {:<50} {:<15} {:<10}".format(
                type_id, name[:48], price_str, volume
            ))

if __name__ == "__main__":
    main() 