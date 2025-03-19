"""
Production Service for EVE Frontier Blueprint Miracle.

This module provides functionality to analyze production chains, calculate costs,
and optimize manufacturing processes.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from decimal import Decimal

from sqlalchemy.orm import Session

from eve_frontier.models import (
    Item, 
    Blueprint, 
    BlueprintActivity, 
    BlueprintMaterial,
    SkillRequirement,
    BlueprintProduct
)

logger = logging.getLogger(__name__)


class ProductionChainNode:
    """Represents a node in a production chain."""
    
    def __init__(
        self, 
        item_id: int, 
        item_name: str, 
        quantity: int,
        blueprint_id: Optional[int] = None,
        activity_id: Optional[int] = None,
        activity_name: Optional[str] = None,
        materials: Optional[List['ProductionChainNode']] = None,
        buy_price: Optional[Decimal] = None,
        sell_price: Optional[Decimal] = None,
        production_cost: Optional[Decimal] = None,
        time_required: Optional[int] = None,  # in seconds
    ):
        """
        Initialize a production chain node.
        
        Args:
            item_id: ID of the item
            item_name: Name of the item
            quantity: Quantity needed
            blueprint_id: Optional ID of the blueprint
            activity_id: Optional ID of the activity
            activity_name: Optional name of the activity
            materials: Optional list of child nodes (materials)
            buy_price: Optional buy price of the item
            sell_price: Optional sell price of the item
            production_cost: Optional cost to produce this item
            time_required: Optional time required to produce this item (in seconds)
        """
        self.item_id = item_id
        self.item_name = item_name
        self.quantity = quantity
        self.blueprint_id = blueprint_id
        self.activity_id = activity_id
        self.activity_name = activity_name
        self.materials = materials or []
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.production_cost = production_cost
        self.time_required = time_required
    
    def total_buy_cost(self) -> Optional[Decimal]:
        """Calculate the total cost to buy this item."""
        if self.buy_price is None:
            return None
        return self.buy_price * Decimal(self.quantity)
    
    def total_production_cost(self) -> Optional[Decimal]:
        """Calculate the total cost to produce this item."""
        if self.production_cost is None:
            return None
        return self.production_cost * Decimal(self.quantity)
    
    def to_dict(self) -> Dict:
        """Convert the node to a dictionary for serialization."""
        result = {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "blueprint_id": self.blueprint_id,
            "activity_id": self.activity_id,
            "activity_name": self.activity_name,
            "buy_price": float(self.buy_price) if self.buy_price is not None else None,
            "sell_price": float(self.sell_price) if self.sell_price is not None else None,
            "production_cost": float(self.production_cost) if self.production_cost is not None else None,
            "time_required": self.time_required,
            "materials": [m.to_dict() for m in self.materials],
        }
        return result


class ProductionService:
    """Service for analyzing production chains and manufacturing calculations."""
    
    def __init__(self, db: Session):
        """
        Initialize the ProductionService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_manufacturing_details(
        self, 
        item_id: int, 
        quantity: int = 1,
        me_level: int = 0,  # Material Efficiency level
        te_level: int = 0,  # Time Efficiency level
        facility_bonus: float = 0.0,  # Facility bonus reduction (0.0 to 1.0)
        max_depth: int = 3,  # Maximum depth of the production chain
        ignore_items: Optional[List[int]] = None,  # Items to consider as "buy"
    ) -> Optional[ProductionChainNode]:
        """
        Get manufacturing details for an item, including its production chain.
        
        Args:
            item_id: ID of the item
            quantity: Quantity to manufacture
            me_level: Material Efficiency level of the blueprint (0-10)
            te_level: Time Efficiency level of the blueprint (0-20)
            facility_bonus: Facility bonus reduction (0.0 to 1.0)
            max_depth: Maximum depth of the production chain to calculate
            ignore_items: List of item IDs to ignore for manufacturing (buy instead)
            
        Returns:
            A ProductionChainNode representing the root of the production chain,
            or None if the item cannot be manufactured
        """
        logger.debug(f"Getting manufacturing details for item_id={item_id}, quantity={quantity}")
        
        # Avoid circular dependencies by tracking processed items
        processed_items = set(ignore_items or [])
        
        # Get the item
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item:
            logger.warning(f"Item with ID {item_id} not found")
            return None
        
        # Check if this is a manufacturable item
        blueprint = self._find_manufacturing_blueprint(item_id)
        
        # If no blueprint found or we hit max depth, return a market-based node
        if not blueprint or max_depth <= 0:
            if not blueprint:
                logger.info(f"No manufacturing blueprint found for item_id={item_id}")
            
            # Get market data for this item from MarketService
            from eve_frontier.services.market_service import MarketService
            market_service = MarketService(self.db)
            market_stats = market_service.get_market_statistics(item_id, days=1)
            
            buy_price = Decimal(str(market_stats.get('buy_price', 0))) if market_stats else Decimal('0')
            sell_price = Decimal(str(market_stats.get('sell_price', 0))) if market_stats else Decimal('0')
            
            # Return a node with market data
            return ProductionChainNode(
                item_id=item_id,
                item_name=item.name,
                quantity=quantity,
                blueprint_id=None,
                activity_id=None,
                activity_name=None,
                materials=[],
                buy_price=buy_price,
                sell_price=sell_price,
                production_cost=buy_price,  # Use buy price as production cost for raw materials
                time_required=None,
            )
        
        # Get the manufacturing activity
        manufacturing_activity = self._get_manufacturing_activity(blueprint.id)
        if not manufacturing_activity:
            logger.warning(f"No manufacturing activity found for blueprint_id={blueprint.id}")
            return None
        
        # Calculate adjusted time (placeholder calculation)
        base_time = manufacturing_activity.time
        # A basic time efficiency formula (placeholder)
        adjusted_time = base_time * (1 - min(0.2 * te_level, 0.8)) * (1 - facility_bonus)
        
        # Process materials if we haven't hit max depth
        materials_nodes = []
        if max_depth > 0 and item_id not in processed_items:
            # Add current item to processed to prevent cycles
            processed_items.add(item_id)
            
            # Get the materials for this blueprint's manufacturing activity
            materials = self._get_blueprint_materials(blueprint.id, manufacturing_activity.id)
            
            for material in materials:
                # Calculate adjusted quantity
                adjusted_quantity = material.quantity
                
                # Apply material efficiency (placeholder formula)
                if me_level > 0:
                    # A basic material efficiency formula (placeholder)
                    efficiency_factor = max(0.9, 1.0 - (0.02 * me_level))
                    adjusted_quantity = int(adjusted_quantity * efficiency_factor)
                
                # Multiply by requested quantity
                total_quantity = adjusted_quantity * quantity
                
                # Process this material recursively if it's not in the ignore list
                if material.material_id not in processed_items:
                    material_node = self.get_manufacturing_details(
                        item_id=material.material_id,
                        quantity=total_quantity,
                        me_level=me_level,
                        te_level=te_level,
                        facility_bonus=facility_bonus,
                        max_depth=max_depth - 1,
                        ignore_items=list(processed_items)
                    )
                    
                    if material_node:
                        materials_nodes.append(material_node)

        # Get market data for this item
        from eve_frontier.services.market_service import MarketService
        market_service = MarketService(self.db)
        market_stats = market_service.get_market_statistics(item_id, days=1)
        
        buy_price = Decimal(str(market_stats.get('buy_price', 0))) if market_stats else Decimal('0')
        sell_price = Decimal(str(market_stats.get('sell_price', 0))) if market_stats else Decimal('0')
        
        # Calculate production cost based on material costs
        production_cost = Decimal('0')
        if materials_nodes:
            for material_node in materials_nodes:
                # Use the material's production cost if available, otherwise use market buy price
                material_cost = material_node.production_cost or material_node.buy_price or Decimal('0')
                production_cost += material_cost * Decimal(material_node.quantity)
        else:
            # If no materials (or they couldn't be processed), use market price
            production_cost = buy_price * Decimal(quantity)
        
        # Create and return the production chain node
        return ProductionChainNode(
            item_id=item_id,
            item_name=item.name,
            quantity=quantity,
            blueprint_id=blueprint.id if blueprint else None,
            activity_id=manufacturing_activity.id if manufacturing_activity else None,
            activity_name=manufacturing_activity.activity_name if manufacturing_activity else None,
            materials=materials_nodes,
            buy_price=buy_price,
            sell_price=sell_price,
            production_cost=production_cost / Decimal(quantity) if quantity > 0 else Decimal('0'),
            time_required=adjusted_time if manufacturing_activity else None,
        )
    
    def _find_manufacturing_blueprint(self, product_id: int) -> Optional[Blueprint]:
        """
        Find a blueprint that can manufacture the specified item.
        
        Args:
            product_id: ID of the product item
            
        Returns:
            Blueprint object if found, None otherwise
        """
        # First, check if any blueprint products exist for this item
        product_count = (
            self.db.query(BlueprintProduct)
            .filter(BlueprintProduct.product_id == product_id)
            .count()
        )
        
        logger.debug(f"Found {product_count} blueprint products for product_id={product_id}")
        
        if product_count == 0:
            return None
        
        # If products exist, find the blueprint
        blueprint = (
            self.db.query(Blueprint)
            .join(BlueprintProduct, Blueprint.id == BlueprintProduct.blueprint_id)
            .filter(
                BlueprintProduct.product_id == product_id
            )
            .first()
        )
        
        if blueprint:
            logger.debug(f"Found blueprint ID {blueprint.id} ({blueprint.name}) for product_id={product_id}")
        else:
            logger.debug(f"No blueprint found for product_id={product_id}")
        
        return blueprint
    
    def _get_manufacturing_activity(self, blueprint_id: int) -> Optional[BlueprintActivity]:
        """
        Get the manufacturing activity for a blueprint.
        
        Args:
            blueprint_id: ID of the blueprint
            
        Returns:
            BlueprintActivity object if found, None otherwise
        """
        activity = (
            self.db.query(BlueprintActivity)
            .filter(
                BlueprintActivity.blueprint_id == blueprint_id,
                BlueprintActivity.activity_name == "manufacturing"
            )
            .first()
        )
        return activity
    
    def _get_blueprint_materials(
        self, 
        blueprint_id: int, 
        activity_id: int
    ) -> List[BlueprintMaterial]:
        """
        Get the materials required for a blueprint activity.
        
        Args:
            blueprint_id: ID of the blueprint
            activity_id: ID of the activity
            
        Returns:
            List of BlueprintMaterial objects
        """
        materials = (
            self.db.query(BlueprintMaterial)
            .filter(
                BlueprintMaterial.blueprint_id == blueprint_id
            )
            .all()
        )
        return materials
    
    def get_skill_requirements(
        self, 
        blueprint_id: int, 
        activity_id: Optional[int] = None
    ) -> List[SkillRequirement]:
        """
        Get skill requirements for a blueprint and optionally a specific activity.
        
        Args:
            blueprint_id: ID of the blueprint
            activity_id: Optional ID of the activity to filter by
            
        Returns:
            List of SkillRequirement objects
        """
        query = (
            self.db.query(SkillRequirement)
            .filter(SkillRequirement.blueprint_id == blueprint_id)
        )
        
        if activity_id is not None:
            query = query.filter(SkillRequirement.activity_id == activity_id)
        
        return query.all()
    
    def calculate_production_profit(
        self, 
        item_id: int,
        quantity: int = 1,
        me_level: int = 0,
        include_components: bool = True,
    ) -> Dict[str, Union[Decimal, int, float]]:
        """
        Calculate the profit for producing an item.
        
        Args:
            item_id: ID of the item
            quantity: Quantity to produce
            me_level: Material Efficiency level
            include_components: Whether to include the component breakdown
            
        Returns:
            Dictionary with profit information
        """
        try:
            # Get market data for the item
            from eve_frontier.services.market_service import MarketService
            market_service = MarketService(self.db)
            
            # Get market statistics for this item
            market_stats = market_service.get_market_statistics(item_id, days=1)
            if not market_stats or not market_stats.get('sell_price'):
                logger.warning(f"No market data for item {item_id}")
                return None
            
            # Get the market price (lowest sell price)
            market_price = Decimal(str(market_stats.get('sell_price', 0)))
            if market_price <= 0:
                logger.warning(f"Item {item_id} has zero or negative market price")
                return None
            
            # Get the manufacturing details for the item
            production_chain = self.get_manufacturing_details(
                item_id=item_id,
                quantity=quantity,
                me_level=me_level,
                max_depth=3 if include_components else 1
            )
            
            if not production_chain:
                logger.warning(f"No production chain found for item {item_id}")
                return None
            
            # Calculate total production cost
            production_cost = production_chain.total_production_cost()
            if not production_cost:
                logger.warning(f"Could not calculate production cost for item {item_id}")
                return None
            
            # Calculate profit
            profit = market_price * quantity - production_cost
            
            # Calculate profit margin
            profit_margin = (profit / production_cost) * 100 if production_cost > 0 else 0
            
            # Get production time
            production_time = production_chain.time_required or 0
            
            # Calculate profit per hour
            profit_per_hour = (profit / Decimal(production_time)) * 3600 if production_time > 0 else 0
            
            # Get daily volume from market stats
            daily_volume = market_stats.get('daily_volume', 0)
            
            # Create result dictionary
            result = {
                "item_id": item_id,
                "quantity": quantity,
                "production_cost": production_cost,
                "market_price": market_price,
                "profit": profit,
                "profit_margin": float(profit_margin),
                "profit_per_hour": profit_per_hour,
                "production_time": production_time,
                "daily_volume": daily_volume,
            }
            
            # Add components if requested
            if include_components:
                result["components"] = production_chain.to_dict().get('materials', [])
            
            logger.debug(f"Profit calculation for item {item_id}: cost={production_cost}, price={market_price}, profit={profit}, margin={profit_margin}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating production profit for item {item_id}: {e}", exc_info=True)
            return None 