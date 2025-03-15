"""
Market Service for EVE Frontier Blueprint Miracle.

This module provides functionality to retrieve, analyze, and process market data
for items in EVE Online.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from decimal import Decimal
import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from eve_frontier.models import Item, MarketData, MarketHistory, TradingHub, MarketOrder

logger = logging.getLogger(__name__)


class MarketService:
    """Service for retrieving and analyzing market data."""
    
    def __init__(self, db: Session):
        """
        Initialize the MarketService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_market_data(
        self, 
        item_id: int, 
        region_id: Optional[int] = None,
        system_id: Optional[int] = None,
        order_type: str = "all",  # "buy", "sell", or "all"
        limit: int = 50
    ) -> List[MarketData]:
        """
        Get market data for an item.
        
        Args:
            item_id: ID of the item
            region_id: Optional ID of the region to filter by
            system_id: Optional ID of the solar system to filter by
            order_type: Type of orders to get ("buy", "sell", or "all")
            limit: Maximum number of results to return
            
        Returns:
            List of MarketData objects
        """
        logger.debug(f"Getting market data for item_id={item_id}, region_id={region_id}, system_id={system_id}")
        
        # Build the base query
        query = self.db.query(MarketData).filter(MarketData.item_id == item_id)
        
        # Add filters
        if region_id is not None:
            query = query.filter(MarketData.region_id == region_id)
        
        if system_id is not None:
            query = query.filter(MarketData.system_id == system_id)
        
        if order_type == "buy":
            # For buy orders, we're interested in the buy price
            query = query.filter(MarketData.buy_price.isnot(None))
        elif order_type == "sell":
            # For sell orders, we're interested in the sell price
            query = query.filter(MarketData.sell_price.isnot(None))
        
        # Order by price (ascending for sell orders, descending for buy orders)
        if order_type == "buy":
            query = query.order_by(MarketData.buy_price.desc())
        else:
            query = query.order_by(MarketData.sell_price.asc())
        
        # Limit the number of results
        query = query.limit(limit)
        
        # Execute the query
        results = query.all()
        logger.debug(f"Found {len(results)} market orders")
        
        return results
    
    def get_market_statistics(
        self, 
        item_id: int, 
        region_id: Optional[int] = None,
        system_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Union[Decimal, int, float]]:
        """
        Get market statistics for an item.
        
        Args:
            item_id: ID of the item
            region_id: Optional ID of the region to filter by
            system_id: Optional ID of the solar system to filter by
            days: Number of days to include in the statistics
            
        Returns:
            Dictionary with market statistics
        """
        logger.debug(f"Getting market statistics for item_id={item_id}, region_id={region_id}, days={days}")
        
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # Get market data
        sell_orders = self.get_market_data(
            item_id=item_id,
            region_id=region_id,
            system_id=system_id,
            order_type="sell",
            limit=100
        )
        
        buy_orders = self.get_market_data(
            item_id=item_id,
            region_id=region_id,
            system_id=system_id,
            order_type="buy",
            limit=100
        )
        
        # Get historical data
        history = self._get_market_history(
            item_id=item_id,
            region_id=region_id,
            cutoff_date=cutoff_date
        )
        
        # Calculate statistics
        min_sell = min([order.sell_price for order in sell_orders]) if sell_orders else Decimal("0")
        max_buy = max([order.buy_price for order in buy_orders]) if buy_orders else Decimal("0")
        spread = min_sell - max_buy if min_sell > 0 and max_buy > 0 else Decimal("0")
        spread_percentage = (spread / min_sell * 100) if min_sell > 0 else Decimal("0")
        
        # Historical volume and price data
        avg_daily_volume = sum([h.volume for h in history]) / max(1, len(history))
        avg_price = sum([h.average_price for h in history]) / max(1, len(history))
        price_trend = self._calculate_price_trend(history)
        
        # Total volume in sell/buy orders
        sell_volume = sum([order.sell_volume for order in sell_orders])
        buy_volume = sum([order.buy_volume for order in buy_orders])
        
        return {
            "item_id": item_id,
            "region_id": region_id,
            "min_sell_price": float(min_sell),
            "max_buy_price": float(max_buy),
            "spread": float(spread),
            "spread_percentage": float(spread_percentage),
            "avg_daily_volume": avg_daily_volume,
            "avg_price": float(avg_price),
            "price_trend": price_trend,
            "sell_order_volume": sell_volume,
            "buy_order_volume": buy_volume,
            "days_analyzed": days,
        }
    
    def _get_market_history(
        self, 
        item_id: int, 
        region_id: Optional[int], 
        cutoff_date: datetime.datetime
    ) -> List[MarketHistory]:
        """
        Get market history for an item.
        
        Args:
            item_id: ID of the item
            region_id: Optional ID of the region to filter by
            cutoff_date: Cutoff date for the history
            
        Returns:
            List of MarketHistory objects
        """
        query = (
            self.db.query(MarketHistory)
            .filter(
                MarketHistory.item_id == item_id,
                MarketHistory.date >= cutoff_date
            )
        )
        
        if region_id is not None:
            query = query.filter(MarketHistory.region_id == region_id)
        
        query = query.order_by(MarketHistory.date.desc())
        
        return query.all()
    
    def _calculate_price_trend(self, history: List[MarketHistory]) -> float:
        """
        Calculate the price trend from historical data.
        
        Args:
            history: List of MarketHistory objects
            
        Returns:
            Price trend as a float (-1.0 to 1.0, where -1.0 is strongly downward and 1.0 is strongly upward)
        """
        if not history or len(history) < 2:
            return 0.0
        
        # Sort by date (oldest to newest)
        sorted_history = sorted(history, key=lambda h: h.date)
        
        # Simple linear regression
        n = len(sorted_history)
        x = list(range(n))
        y = [float(h.average_price) for h in sorted_history]
        
        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        # Calculate slope (m) and correlation (r)
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        slope = numerator / denominator_x
        correlation = numerator / (denominator_x * denominator_y) ** 0.5
        
        # Convert to a -1.0 to 1.0 scale
        return max(-1.0, min(1.0, correlation))
    
    def get_trading_hubs(self) -> List[TradingHub]:
        """
        Get a list of trading hubs.
        
        Returns:
            List of TradingHub objects
        """
        return self.db.query(TradingHub).order_by(TradingHub.name).all()
    
    def analyze_potential_trades(
        self, 
        source_region_id: int, 
        destination_region_id: int,
        min_profit_margin: float = 15.0,
        min_daily_volume: int = 10,
        limit: int = 100
    ) -> List[Dict[str, Union[int, str, float, Decimal]]]:
        """
        Analyze potential trades between regions.
        
        Args:
            source_region_id: ID of the source region
            destination_region_id: ID of the destination region
            min_profit_margin: Minimum profit margin percentage
            min_daily_volume: Minimum daily volume
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries with trade information
        """
        logger.debug(f"Analyzing trades from region {source_region_id} to {destination_region_id}")
        
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Query market data for both regions
        # 2. Find items with price disparities
        # 3. Filter by volume and profit margin
        # 4. Sort by profit or ROI
        
        # Return empty list for now
        return [] 