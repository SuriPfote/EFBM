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
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            count = 0
            for category_id, category_data in data.items():
                category = Category(
                    id=int(category_id),
                    name=category_data.get("categoryNameID", "Unknown"),
                    published=category_data.get("published", 0) == 1
                )
                self.db.add(category)
                count += 1
            
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
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            count = 0
            for group_id, group_data in data.items():
                group = Group(
                    id=int(group_id),
                    name=group_data.get("groupNameID", "Unknown"),
                    category_id=group_data.get("categoryID"),
                    published=group_data.get("published", 0) == 1
                )
                self.db.add(group)
                count += 1
            
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
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            count = 0
            for item_id, item_data in data.items():
                item = Item(
                    id=int(item_id),
                    name=item_data.get("typeNameID", "Unknown"),
                    group_id=item_data.get("groupID"),
                    base_price=item_data.get("basePrice", 0.0),
                    volume=item_data.get("volume", 0.0),
                    published=item_data.get("published", 0) == 1,
                )
                self.db.add(item)
                count += 1
                
                # Commit in batches to avoid memory issues
                if count % 1000 == 0:
                    self.db.commit()
            
            self.db.commit()
            logger.info(f"Loaded {count} items")
            return count
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error loading items: {e}")
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
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # The blueprint data is nested under a "blueprints" key
            blueprints_data = data.get("blueprints", {})
            
            count = 0
            for blueprint_id, blueprint_data in blueprints_data.items():
                blueprint = Blueprint(
                    id=int(blueprint_id),
                    name=f"Blueprint {blueprint_id}",  # Default name
                    max_production_limit=blueprint_data.get("maxProductionLimit", 0)
                )
                self.db.add(blueprint)
                
                # Load activities
                activities = blueprint_data.get("activities", {})
                for activity_name, activity_data in activities.items():
                    activity = BlueprintActivity(
                        blueprint_id=int(blueprint_id),
                        activity_name=activity_name,
                        time=activity_data.get("time", 0)
                    )
                    self.db.add(activity)
                    
                    # Load materials for this activity
                    materials = activity_data.get("materials", [])
                    for material in materials:
                        bp_material = BlueprintMaterial(
                            blueprint_id=int(blueprint_id),
                            material_id=material.get("typeID"),
                            quantity=material.get("quantity", 1)
                        )
                        self.db.add(bp_material)
                    
                    # Load products for this activity
                    products = activity_data.get("products", [])
                    for product in products:
                        bp_product = BlueprintProduct(
                            blueprint_id=int(blueprint_id),
                            product_id=product.get("typeID"),
                            quantity=product.get("quantity", 1)
                        )
                        self.db.add(bp_product)
                
                count += 1
                # Commit in batches to avoid memory issues
                if count % 100 == 0:
                    self.db.commit()
            
            self.db.commit()
            logger.info(f"Loaded {count} blueprints")
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
        counts = {}
        
        # Load categories
        categories_file = config.json_dir / "categories.json"
        if categories_file.exists():
            counts["categories"] = self.load_categories(categories_file)
        
        # Load groups
        groups_file = config.json_dir / "groups.json"
        if groups_file.exists():
            counts["groups"] = self.load_groups(groups_file)
        
        # Load items
        items_file = config.json_dir / "types_filtered.json"
        if items_file.exists():
            counts["items"] = self.load_items(items_file)
        
        # Load blueprints
        blueprints_file = config.json_dir / "blueprints.json"
        if blueprints_file.exists():
            counts["blueprints"] = self.load_blueprints(blueprints_file)
        
        return counts 