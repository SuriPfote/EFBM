"""
Search Service for EVE Frontier Blueprint Miracle.

This module provides functionality to search for items, blueprints, and other entities in the database.
"""

import logging
from typing import Dict, List, Optional, Union

from sqlalchemy import or_
from sqlalchemy.orm import Session

from eve_frontier.models import Category, Group, Item, Blueprint

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching for items, blueprints, and other entities in the database."""
    
    def __init__(self, db: Session):
        """
        Initialize the SearchService service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def search_items(
        self, 
        query: str, 
        category_id: Optional[int] = None, 
        group_id: Optional[int] = None,
        published_only: bool = True,
        limit: int = 50
    ) -> List[Item]:
        """
        Search for items matching the query.
        
        Args:
            query: Search query string
            category_id: Optional category ID to filter by
            group_id: Optional group ID to filter by
            published_only: Whether to only return published items
            limit: Maximum number of results to return
            
        Returns:
            List of matching Item objects
        """
        logger.debug(f"Searching for items: query='{query}' category_id={category_id} group_id={group_id}")
        
        # Start with a base query on the Item model
        query_obj = self.db.query(Item)
        
        # Add filters
        if query:
            # Split the query into terms for more flexible searching
            terms = query.strip().lower().split()
            
            # Start with no filter conditions
            filter_conditions = []
            
            # Create filter condition for each term
            for term in terms:
                filter_conditions.append(Item.name.ilike(f'%{term}%'))
            
            # Combine with OR - item must match any of the terms
            if filter_conditions:
                query_obj = query_obj.filter(or_(*filter_conditions))
        
        # Filter by category if specified
        if category_id is not None:
            query_obj = query_obj.join(Group).filter(Group.category_id == category_id)
        
        # Filter by group if specified
        if group_id is not None:
            query_obj = query_obj.filter(Item.group_id == group_id)
        
        # Filter by published status if requested
        if published_only:
            query_obj = query_obj.filter(Item.published == True)
        
        # Order by name
        query_obj = query_obj.order_by(Item.name)
        
        # Limit the number of results
        query_obj = query_obj.limit(limit)
        
        # Execute the query
        results = query_obj.all()
        logger.debug(f"Found {len(results)} items matching query")
        
        return results
    
    def search_blueprints(
        self, 
        query: str, 
        activity_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Blueprint]:
        """
        Search for blueprints matching the query.
        
        Args:
            query: Search query string
            activity_name: Optional activity name to filter by (e.g., "manufacturing")
            limit: Maximum number of results to return
            
        Returns:
            List of matching Blueprint objects
        """
        logger.debug(f"Searching for blueprints: query='{query}' activity_name={activity_name}")
        
        # This implementation is a simplified placeholder
        # Real implementation would likely join with activities and filter
        
        # Start with a base query on the Blueprint model
        query_obj = self.db.query(Blueprint)
        
        # Add filters
        if query:
            query_obj = query_obj.filter(Blueprint.name.ilike(f'%{query}%'))
        
        # Order by name
        query_obj = query_obj.order_by(Blueprint.name)
        
        # Limit the number of results
        query_obj = query_obj.limit(limit)
        
        # Execute the query
        results = query_obj.all()
        logger.debug(f"Found {len(results)} blueprints matching query")
        
        return results
    
    def get_categories(self, published_only: bool = True) -> List[Category]:
        """
        Get all categories.
        
        Args:
            published_only: Whether to only return published categories
            
        Returns:
            List of Category objects
        """
        query = self.db.query(Category)
        
        if published_only:
            query = query.filter(Category.published == True)
        
        return query.order_by(Category.name).all()
    
    def get_groups(
        self, 
        category_id: Optional[int] = None, 
        published_only: bool = True
    ) -> List[Group]:
        """
        Get all groups, optionally filtered by category.
        
        Args:
            category_id: Optional category ID to filter by
            published_only: Whether to only return published groups
            
        Returns:
            List of Group objects
        """
        query = self.db.query(Group)
        
        if category_id is not None:
            query = query.filter(Group.category_id == category_id)
        
        if published_only:
            query = query.filter(Group.published == True)
        
        return query.order_by(Group.name).all() 