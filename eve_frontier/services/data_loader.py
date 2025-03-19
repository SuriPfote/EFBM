"""
Data Loader service for EVE Frontier Blueprint Miracle.

This module provides functionality to load data from JSON files and store it in the database.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from sqlalchemy.orm import Session

from eve_frontier.config import config
from eve_frontier.models import (
    Base, Category, Group, Item, Blueprint, 
    BlueprintProduct, BlueprintMaterial, BlueprintActivity
)

logger = logging.getLogger(__name__)


class DataLoader:
    """Service for loading data from JSON files into the database."""
    
    def __init__(self, db: Session):
        """
        Initialize the DataLoader service.
        
        Args:
            db: SQLAlchemy database session
        """
        logger.debug("Initializing DataLoader with database session")
        self.db = db
    
    def load_categories(self, file_path: Union[str, Path]) -> int:
        """
        Load categories from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Number of categories loaded
        """
        logger.info(f"Loading categories from {file_path}")
        try:
            logger.debug(f"Opening file {file_path} for reading")
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded JSON data with {len(data)} categories")
            
            count = 0
            for category_id, category_data in data.items():
                logger.debug(f"Processing category ID {category_id}: {category_data}")
                category = Category(
                    id=int(category_id),
                    name=category_data.get("categoryNameID", "Unknown"),
                    published=category_data.get("published", 0) == 1
                )
                logger.debug(f"Created category: {category.id} - {category.name} (published: {category.published})")
                self.db.add(category)
                count += 1
            
            logger.debug(f"Committing {count} categories to database")
            self.db.commit()
            logger.info(f"Loaded {count} categories")
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error loading categories: {e}")
            raise
    
    def load_groups(self, file_path: Union[str, Path]) -> int:
        """
        Load groups from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Number of groups loaded
        """
        logger.info(f"Loading groups from {file_path}")
        try:
            logger.debug(f"Opening file {file_path} for reading")
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded JSON data with {len(data)} groups")
            
            count = 0
            for group_id, group_data in data.items():
                logger.debug(f"Processing group ID {group_id}: {group_data}")
                group = Group(
                    id=int(group_id),
                    name=group_data.get("groupNameID", "Unknown"),
                    category_id=group_data.get("categoryID"),
                    published=group_data.get("published", 0) == 1
                )
                logger.debug(f"Created group: {group.id} - {group.name} (category: {group.category_id}, published: {group.published})")
                self.db.add(group)
                count += 1
            
            logger.debug(f"Committing {count} groups to database")
            self.db.commit()
            logger.info(f"Loaded {count} groups")
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error loading groups: {e}")
            raise
    
    def load_items(self, file_path: Union[str, Path]) -> int:
        """
        Load items from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Number of items loaded
        """
        logger.info(f"Loading items from {file_path}")
        try:
            # Load the JSON data
            logger.debug(f"Opening file {file_path} for reading")
            with open(file_path, 'r') as f:
                items_data = json.load(f)

            # Process the items
            logger.info(f"Processing {len(items_data)} items")
            logger.debug(f"First 5 item IDs: {list(items_data.keys())[:5]}")
            
            # Create a batch for database operations
            items_batch = []
            
            processed_count = 0
            for type_id, item_data in items_data.items():
                # Get the name from typeNameID which already contains the human-readable name
                type_id = int(type_id)
                # Instead of using typeNameID as the numeric ID, use it as the actual name
                name = item_data.get('typeNameID', str(type_id))
                
                group_id = item_data.get('groupID')
                base_price = item_data.get('basePrice', 0)
                volume = item_data.get('volume', 0)
                published = bool(item_data.get('published', False))
                
                logger.debug(f"Processing item ID {type_id}: name={name}, group_id={group_id}, base_price={base_price}, volume={volume}, published={published}")
                
                # Create a new Item object
                item = Item(
                    id=type_id,
                    name=name,  # Use the name we extracted above
                    group_id=group_id,
                    base_price=base_price,
                    volume=volume,
                    published=published
                )
                
                # Add the item to the batch
                items_batch.append(item)
                processed_count += 1
                
                # Commit in batches of 100 to avoid memory issues
                if len(items_batch) >= 100:
                    logger.debug(f"Committing batch of {len(items_batch)} items (total processed: {processed_count}/{len(items_data)})")
                    self.db.add_all(items_batch)
                    self.db.commit()
                    items_batch = []
            
            # Commit any remaining items
            if items_batch:
                logger.debug(f"Committing final batch of {len(items_batch)} items (total processed: {processed_count}/{len(items_data)})")
                self.db.add_all(items_batch)
                self.db.commit()
            
            logger.info(f"Successfully loaded {len(items_data)} items")
            return len(items_data)
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error loading items: {str(e)}")
            raise
    
    def load_blueprints(self, file_path: Union[str, Path]) -> int:
        """
        Load blueprints from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Number of blueprints loaded
        """
        logger.info(f"Loading blueprints from {file_path}")
        try:
            logger.debug(f"Opening file {file_path} for reading")
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # The blueprint data is nested under a "blueprints" key
            blueprints_data = data.get("blueprints", {})
            logger.debug(f"Loaded JSON data with {len(blueprints_data)} blueprints")
            logger.debug(f"First 5 blueprint IDs: {list(blueprints_data.keys())[:5]}")
            
            # Load item names for better blueprint naming
            logger.debug("Loading item names from database for blueprint naming")
            item_names = {}
            items = self.db.query(Item).all()
            for item in items:
                item_names[item.id] = item.name
            logger.debug(f"Loaded {len(item_names)} item names")
            
            count = 0
            materials_count = 0
            products_count = 0
            activities_count = 0
            
            for blueprint_id, blueprint_data in blueprints_data.items():
                # Try to find a product name for a better blueprint name
                blueprint_name = f"Blueprint {blueprint_id}"  # Default name
                
                # Check manufacturing activities for products
                activities = blueprint_data.get("activities", {})
                manufacturing = activities.get("manufacturing", {})
                if manufacturing:
                    products = manufacturing.get("products", [])
                    if products:
                        # Use the first product's name for the blueprint name
                        product_id = products[0].get("typeID")
                        if product_id in item_names:
                            blueprint_name = f"{item_names[product_id]} Blueprint"
                
                logger.debug(f"Processing blueprint ID {blueprint_id}: name={blueprint_name}")
                
                blueprint = Blueprint(
                    id=int(blueprint_id),
                    name=blueprint_name,
                    max_production_limit=blueprint_data.get("maxProductionLimit", 0)
                )
                self.db.add(blueprint)
                
                # Load activities
                activities = blueprint_data.get("activities", {})
                logger.debug(f"Blueprint {blueprint_id} has {len(activities)} activities: {list(activities.keys())}")
                
                for activity_name, activity_data in activities.items():
                    logger.debug(f"Processing activity '{activity_name}' for blueprint {blueprint_id}")
                    activity = BlueprintActivity(
                        blueprint_id=int(blueprint_id),
                        activity_name=activity_name,
                        time=activity_data.get("time", 0)
                    )
                    self.db.add(activity)
                    activities_count += 1
                    
                    # Load materials for this activity
                    materials = activity_data.get("materials", [])
                    logger.debug(f"Activity '{activity_name}' has {len(materials)} materials")
                    
                    for material in materials:
                        material_id = material.get("typeID")
                        quantity = material.get("quantity", 1)
                        material_name = item_names.get(material_id, f"Unknown Material {material_id}")
                        
                        logger.debug(f"Adding material: {material_id} ({material_name}) x{quantity}")
                        
                        bp_material = BlueprintMaterial(
                            blueprint_id=int(blueprint_id),
                            material_id=material_id,
                            quantity=quantity
                        )
                        self.db.add(bp_material)
                        materials_count += 1
                    
                    # Load products for this activity
                    products = activity_data.get("products", [])
                    logger.debug(f"Activity '{activity_name}' has {len(products)} products")
                    
                    for product in products:
                        product_id = product.get("typeID")
                        quantity = product.get("quantity", 1)
                        product_name = item_names.get(product_id, f"Unknown Product {product_id}")
                        
                        logger.debug(f"Adding product: {product_id} ({product_name}) x{quantity}")
                        
                        bp_product = BlueprintProduct(
                            blueprint_id=int(blueprint_id),
                            product_id=product_id,
                            quantity=quantity
                        )
                        self.db.add(bp_product)
                        products_count += 1
                
                count += 1
                # Commit in batches to avoid memory issues
                if count % 100 == 0:
                    logger.debug(f"Committing batch after processing {count} blueprints")
                    self.db.commit()
            
            logger.debug(f"Final commit for {count} blueprints")
            self.db.commit()
            logger.info(f"Loaded {count} blueprints with {activities_count} activities, {materials_count} materials, and {products_count} products")
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error loading blueprints: {e}")
            raise
    
    def load_all(self) -> Dict[str, int]:
        """
        Load all data from JSON files into the database.
        
        Returns:
            Dictionary with counts of loaded entities
        """
        logger.info("Loading all data from JSON files")
        counts = {}
        
        # Load categories
        categories_file = config.json_dir / "categories.json"
        if categories_file.exists():
            logger.debug(f"Categories file exists at {categories_file}")
            counts["categories"] = self.load_categories(categories_file)
        else:
            logger.warning(f"Categories file not found at {categories_file}")
        
        # Load groups
        groups_file = config.json_dir / "groups.json"
        if groups_file.exists():
            logger.debug(f"Groups file exists at {groups_file}")
            counts["groups"] = self.load_groups(groups_file)
        else:
            logger.warning(f"Groups file not found at {groups_file}")
        
        # Load items
        items_file = config.json_dir / "types_filtered.json"
        if items_file.exists():
            logger.debug(f"Items file exists at {items_file}")
            counts["items"] = self.load_items(items_file)
        else:
            logger.warning(f"Items file not found at {items_file}")
        
        # Load blueprints (use filtered version)
        blueprints_file = config.json_dir / "blueprints_filtered.json"
        if not blueprints_file.exists():
            logger.warning(f"Filtered blueprints file not found at {blueprints_file}. Falling back to original blueprints.json")
            blueprints_file = config.json_dir / "blueprints.json"
        
        if blueprints_file.exists():
            logger.debug(f"Blueprints file exists at {blueprints_file}")
            counts["blueprints"] = self.load_blueprints(blueprints_file)
        else:
            logger.warning(f"Blueprints file not found at {blueprints_file}")
        
        logger.info(f"Finished loading all data: {counts}")
        return counts 