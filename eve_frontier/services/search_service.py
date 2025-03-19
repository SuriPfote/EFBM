"""
Search Service for EVE Frontier Blueprint Miracle.

This module provides functionality to search for items, blueprints, and other entities in the database.
"""

import logging
from typing import Dict, List, Optional, Union

from sqlalchemy import or_, func
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
        
        if not query:
            # If no query is provided, return all items (with filters)
            return self._filter_items_query(None, category_id, group_id, published_only, limit).all()
        
        # Normalize the query
        normalized_query = query.strip().lower()
        
        # First, try to find exact matches (case-insensitive)
        exact_matches = self._filter_items_query(
            Item.name.ilike(normalized_query),
            category_id, 
            group_id, 
            published_only, 
            limit
        ).all()
        
        if exact_matches:
            logger.debug(f"Found {len(exact_matches)} exact matches for '{query}'")
            return exact_matches
        
        # Next, try to find items that start with the query
        starts_with_matches = self._filter_items_query(
            Item.name.ilike(f"{normalized_query}%"),
            category_id, 
            group_id, 
            published_only, 
            limit
        ).all()
        
        if starts_with_matches:
            logger.debug(f"Found {len(starts_with_matches)} starts-with matches for '{query}'")
            return starts_with_matches
        
        # If no exact or starts-with matches, try with individual terms
        terms = normalized_query.split()
        
        if len(terms) > 1:
            # Try to find items containing all terms (AND)
            all_terms_filter = []
            for term in terms:
                all_terms_filter.append(Item.name.ilike(f"%{term}%"))
            
            all_terms_matches = self._filter_items_query(
                *all_terms_filter,
                category_id=category_id, 
                group_id=group_id, 
                published_only=published_only, 
                limit=limit
            ).all()
            
            if all_terms_matches:
                logger.debug(f"Found {len(all_terms_matches)} all-terms matches for '{query}'")
                return all_terms_matches
        
        # Finally, fallback to the original OR-based approach
        filter_conditions = []
        for term in terms:
            filter_conditions.append(Item.name.ilike(f"%{term}%"))
        
        any_term_matches = self._filter_items_query(
            or_(*filter_conditions) if filter_conditions else None,
            category_id, 
            group_id, 
            published_only, 
            limit
        ).all()
        
        logger.debug(f"Found {len(any_term_matches)} any-term matches for '{query}'")
        return any_term_matches
    
    def _filter_items_query(
        self,
        name_filter=None,
        category_id=None,
        group_id=None,
        published_only=True,
        limit=50
    ):
        """
        Create a filtered query for items.
        
        Args:
            name_filter: Name filter condition
            category_id: Optional category ID to filter by
            group_id: Optional group ID to filter by
            published_only: Whether to only return published items
            limit: Maximum number of results to return
            
        Returns:
            Filtered SQLAlchemy query object
        """
        # Start with a base query on the Item model
        query_obj = self.db.query(Item)
        
        # Add name filter if provided
        if name_filter is not None:
            if isinstance(name_filter, list):
                for f in name_filter:
                    query_obj = query_obj.filter(f)
            else:
                query_obj = query_obj.filter(name_filter)
        
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
        if limit:
            query_obj = query_obj.limit(limit)
        
        return query_obj
    
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