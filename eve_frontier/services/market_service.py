"""
Market Service for EVE Frontier Blueprint Miracle.

This module provides functionality to retrieve, analyze, and process market data
for items in EVE Online.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from decimal import Decimal
import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from eve_frontier.models import Item, MarketData, MarketHistory, TradingHub, MarketOrder
from eve_frontier.services.market_log_parser import MarketLogParser

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
        
        # Initialize the market log parser
        self.market_log_parser = MarketLogParser(
            log_directory="data/csv/Marketlogs",
            cache_directory="data/refined_market_data"
        )
        
        # Load unified market data
        self._unified_market_data = None
        
    def get_unified_market_data(self) -> Dict:
        """
        Get the unified market data.
        This is a public accessor for the protected _load_unified_market_data method.
        
        Returns:
            Dictionary containing unified market data
        """
        return self._load_unified_market_data()
        
    def _load_unified_market_data(self):
        """Load unified market data if not already loaded."""
        if self._unified_market_data is None:
            logger.info("Loading unified market data")
            # Try to load from cache first
            try:
                cached_data = self.market_log_parser.load_cached_data("unified_market_data")
                
                if cached_data:
                    item_count = len(cached_data.get('items', {}))
                    trading_hub_count = len(cached_data.get('trading_hubs', []))
                    logger.info(f"Loaded cached market data: {item_count} items, {trading_hub_count} trading hubs")
                    
                    # Log a few item IDs for debugging
                    item_ids = list(cached_data.get('items', {}).keys())
                    logger.debug(f"Available item IDs: {item_ids[:10]}...")
                    
                    # Log trading hub info
                    for i, hub in enumerate(cached_data.get('trading_hubs', [])[:5]):
                        logger.debug(f"Trading hub {i+1}: ID={hub.get('id')}, Name={hub.get('name')}")
                    
                    self._unified_market_data = cached_data
                else:
                    logger.info("No cached market data found, parsing all logs")
                    # Parse all market logs
                    self._unified_market_data = self.market_log_parser.parse_all_logs()
                    
                    if self._unified_market_data:
                        item_count = len(self._unified_market_data.get('items', {}))
                        logger.info(f"Parsed {item_count} items from market logs")
                    else:
                        logger.warning("Failed to parse market logs, no data available")
            except Exception as e:
                logger.error(f"Error loading unified market data: {e}", exc_info=True)
                return None
                
        return self._unified_market_data
            
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
        logger.info(f"Getting market data for item_id={item_id}, order_type={order_type}, region_id={region_id}, system_id={system_id}")
        
        # First try to get data from the database
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
        
        try:
            # Execute the query
            db_results = query.all()
            
            # If we have results from the database, return them
            if db_results:
                logger.info(f"Found {len(db_results)} market orders in database")
                return db_results
        except Exception as e:
            logger.error(f"Database query error: {e}", exc_info=True)
        
        # Otherwise, try to get data from market logs
        logger.info(f"No database results for item_id={item_id}, using market logs")
        try:
            # Load unified market data
            market_data = self._load_unified_market_data()
            if not market_data:
                logger.error("Failed to load unified market data")
                return []
                
            # Log what items we have data for
            available_items = list(market_data.get('items', {}).keys())
            logger.debug(f"Unified market data contains {len(available_items)} items: {available_items[:10]}...")
            
            # Get orders for this item
            str_item_id = str(item_id)
            item_data = market_data.get('items', {}).get(str_item_id)
            
            if not item_data:
                logger.warning(f"No market data found for item_id={item_id} in unified market data")
                return []
                
            logger.debug(f"Found item data for {item_data.get('name', 'unknown')} (ID: {item_id})")
            
            # Get orders based on order type
            orders = []
            if order_type == "buy" or order_type == "all":
                buy_orders = item_data.get('buy_orders', [])
                logger.debug(f"Found {len(buy_orders)} buy orders for item_id={item_id}")
                
                # Filter by region if specified
                if region_id is not None:
                    buy_orders = [o for o in buy_orders if o.get('region_id') == region_id]
                    logger.debug(f"After region filter: {len(buy_orders)} buy orders remain")
                
                # Filter by system if specified
                if system_id is not None:
                    buy_orders = [o for o in buy_orders if o.get('solar_system_id') == system_id]
                    logger.debug(f"After system filter: {len(buy_orders)} buy orders remain")
                
                # Log details of first few orders for debugging
                for i, order in enumerate(buy_orders[:3]):
                    logger.debug(f"Buy order {i+1}: ID={order.get('order_id')}, Price={order.get('price')}, "
                                 f"Volume={order.get('volume_remaining')}, Station={order.get('station_id')}")
                
                # Convert to MarketData objects
                for order in buy_orders[:limit]:
                    try:
                        issue_date = order.get('issue_date', '')
                        # Handle potential format issues with the timestamp
                        try:
                            if 'T' not in issue_date and ' ' in issue_date:
                                timestamp = datetime.datetime.fromisoformat(issue_date.replace(' ', 'T'))
                            else:
                                timestamp = datetime.datetime.fromisoformat(issue_date)
                        except ValueError:
                            logger.warning(f"Invalid date format: {issue_date}, using current time")
                            timestamp = datetime.datetime.utcnow()
                            
                        market_data = MarketData(
                            id=order.get('order_id', 0),  # Using order_id as a placeholder ID
                            item_id=item_id,
                            station_id=order.get('station_id'),
                            buy_price=order.get('price'),
                            sell_price=None,
                            buy_volume=order.get('volume_remaining'),
                            sell_volume=None,
                            timestamp=timestamp
                        )
                        orders.append(market_data)
                    except Exception as e:
                        logger.warning(f"Error creating MarketData object from buy order: {e}")
            
            if order_type == "sell" or order_type == "all":
                sell_orders = item_data.get('sell_orders', [])
                logger.debug(f"Found {len(sell_orders)} sell orders for item_id={item_id}")
                
                # Filter by region if specified
                if region_id is not None:
                    sell_orders = [o for o in sell_orders if o.get('region_id') == region_id]
                    logger.debug(f"After region filter: {len(sell_orders)} sell orders remain")
                
                # Filter by system if specified
                if system_id is not None:
                    sell_orders = [o for o in sell_orders if o.get('solar_system_id') == system_id]
                    logger.debug(f"After system filter: {len(sell_orders)} sell orders remain")
                
                # Log details of first few orders for debugging
                for i, order in enumerate(sell_orders[:3]):
                    logger.debug(f"Sell order {i+1}: ID={order.get('order_id')}, Price={order.get('price')}, "
                                 f"Volume={order.get('volume_remaining')}, Station={order.get('station_id')}")
                
                # Convert to MarketData objects
                for order in sell_orders[:limit]:
                    try:
                        issue_date = order.get('issue_date', '')
                        # Handle potential format issues with the timestamp
                        try:
                            if 'T' not in issue_date and ' ' in issue_date:
                                timestamp = datetime.datetime.fromisoformat(issue_date.replace(' ', 'T'))
                            else:
                                timestamp = datetime.datetime.fromisoformat(issue_date)
                        except ValueError:
                            logger.warning(f"Invalid date format: {issue_date}, using current time")
                            timestamp = datetime.datetime.utcnow()
                            
                        market_data = MarketData(
                            id=order.get('order_id', 0),  # Using order_id as a placeholder ID
                            item_id=item_id,
                            station_id=order.get('station_id'),
                            buy_price=None,
                            sell_price=order.get('price'),
                            buy_volume=None,
                            sell_volume=order.get('volume_remaining'),
                            timestamp=timestamp
                        )
                        orders.append(market_data)
                    except Exception as e:
                        logger.warning(f"Error creating MarketData object from sell order: {e}")
            
            # Sort and limit
            if order_type == "buy":
                orders.sort(key=lambda o: o.buy_price or 0, reverse=True)
            elif order_type == "sell":
                orders.sort(key=lambda o: o.sell_price or float('inf'))
            
            orders = orders[:limit]
            
            logger.info(f"Returning {len(orders)} market orders from logs for item_id={item_id}")
            return orders
            
        except Exception as e:
            logger.error(f"Error getting market data from logs: {e}", exc_info=True)
            return []
    
    def get_market_statistics(
        self, 
        item_id: int, 
        region_id: Optional[int] = None, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate market statistics for an item.
        
        Args:
            item_id: ID of the item
            region_id: Optional ID of the region to filter by
            days: Number of days of history to include
            
        Returns:
            Dictionary with market statistics
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            system_id = None  # Replace with system filtering if needed
            
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
            
            # Get historical data from database
            history = self._get_market_history(
                item_id=item_id,
                region_id=region_id,
                cutoff_date=cutoff_date
            )
            
            # If we don't have historical data, use the market logs directly
            if not history:
                # Try to get statistics from unified market data
                market_data = self._load_unified_market_data()
                
                str_item_id = str(item_id)
                item_data = market_data.get('items', {}).get(str_item_id, {})
                
                if item_data:
                    stats = item_data.get('statistics', {})
                    min_sell_price = stats.get('min_sell_price', 0) or 0
                    max_buy_price = stats.get('max_buy_price', 0) or 0
                    spread = (min_sell_price - max_buy_price) if min_sell_price > 0 and max_buy_price > 0 else 0
                    
                    # Avoid division by zero
                    spread_percentage = 0
                    if min_sell_price > 0:
                        spread_percentage = (spread / min_sell_price) * 100
                    
                    return {
                        'item_id': item_id,
                        'region_id': region_id,
                        'min_sell_price': min_sell_price,
                        'max_buy_price': max_buy_price,
                        'sell_price': min_sell_price,  # Add sell_price for consistency
                        'buy_price': max_buy_price,    # Add buy_price for consistency
                        'spread': spread,
                        'spread_percentage': spread_percentage,
                        'daily_volume': stats.get('total_sell_volume', 0) / max(1, days),
                        'avg_daily_volume': stats.get('total_sell_volume', 0) / max(1, days),
                        'avg_price': min_sell_price,  # No real average available
                        'price_trend': 0.0,  # No historical data to calculate trend
                        'sell_order_volume': stats.get('total_sell_volume', 0),
                        'buy_order_volume': stats.get('total_buy_volume', 0),
                        'days_analyzed': days,
                    }
            
            # Calculate statistics from the data we have
            min_sell = min([order.sell_price for order in sell_orders if order.sell_price]) if sell_orders else Decimal("0")
            max_buy = max([order.buy_price for order in buy_orders if order.buy_price]) if buy_orders else Decimal("0")
            spread = min_sell - max_buy if min_sell > 0 and max_buy > 0 else Decimal("0")
            
            # Avoid division by zero
            spread_percentage = Decimal("0")
            if min_sell > 0:
                spread_percentage = (spread / min_sell * 100)
            
            # Historical volume and price data
            avg_daily_volume = sum([h.volume for h in history]) / max(1, len(history)) if history else 0
            avg_price = sum([h.average_price for h in history]) / max(1, len(history)) if history else (min_sell or 0)
            price_trend = self._calculate_price_trend(history) if history else 0.0
            
            # Total volume in sell/buy orders
            sell_volume = sum([order.sell_volume for order in sell_orders if order.sell_volume]) if sell_orders else 0
            buy_volume = sum([order.buy_volume for order in buy_orders if order.buy_volume]) if buy_orders else 0
            
            return {
                "item_id": item_id,
                "region_id": region_id,
                "min_sell_price": float(min_sell),
                "max_buy_price": float(max_buy),
                "sell_price": float(min_sell),  # Add sell_price for consistency
                "buy_price": float(max_buy),    # Add buy_price for consistency
                "spread": float(spread),
                "spread_percentage": float(spread_percentage),
                "daily_volume": avg_daily_volume,  # Add daily_volume for consistency
                "avg_daily_volume": avg_daily_volume,
                "avg_price": float(avg_price),
                "price_trend": price_trend,
                "sell_order_volume": sell_volume,
                "buy_order_volume": buy_volume,
                "days_analyzed": days,
            }
        
        except Exception as e:
            logger.error(f"Error calculating market statistics: {e}", exc_info=True)
            
            # Return empty statistics with consistent field names
            return {
                "item_id": item_id,
                "region_id": region_id,
                "min_sell_price": 0.0,
                "max_buy_price": 0.0,
                "sell_price": 0.0,
                "buy_price": 0.0,
                "spread": 0.0,
                "spread_percentage": 0.0,
                "daily_volume": 0,
                "avg_daily_volume": 0,
                "avg_price": 0.0,
                "price_trend": 0.0,
                "sell_order_volume": 0,
                "buy_order_volume": 0,
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
    
    def get_trading_hubs(self) -> List[Union[TradingHub, Dict[str, Any]]]:
        """
        Get a list of trading hubs.
        
        Returns:
            List of TradingHub objects or dictionaries with hub information
        """
        # First try to get trading hubs from the database
        db_hubs = self.db.query(TradingHub).order_by(TradingHub.name).all()
        
        if db_hubs:
            logger.info(f"Found {len(db_hubs)} trading hubs in database")
            return db_hubs
        
        # If no hubs in database, generate from market logs
        try:
            logger.info("No trading hubs in database, getting from market logs")
            # Get trading hubs directly from the MarketLogParser
            hubs = self.market_log_parser.get_trading_hubs()
            
            if hubs:
                logger.info(f"Found {len(hubs)} trading hubs in market logs")
                return hubs
            else:
                logger.warning("No trading hubs found in market logs")
                return []
            
        except Exception as e:
            logger.error(f"Error getting trading hubs from logs: {e}", exc_info=True)
            return []
    
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
    
    def reload_market_data(self) -> bool:
        """
        Force reload market data from log files.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Forcing reload of market data from log files")
        try:
            # Clear the cache and reload from log files
            unified_data = self.market_log_parser.clear_cache_and_reload()
            
            # Update our in-memory cache
            self._unified_market_data = unified_data
            
            # Log some statistics
            item_count = len(unified_data.get('items', {}))
            hub_count = len(unified_data.get('trading_hubs', []))
            logger.info(f"Reloaded market data: {item_count} items, {hub_count} trading hubs")
            
            return True
        except Exception as e:
            logger.error(f"Failed to reload market data: {e}", exc_info=True)
            return False
    
    def batch_get_station_names(self, station_ids: List[int]) -> Dict[int, str]:
        """
        Get multiple station names at once.
        
        Args:
            station_ids: List of station IDs to get names for
            
        Returns:
            Dictionary mapping station IDs to their names
        """
        if not self.market_log_parser:
            logger.warning("Market log parser not initialized when batch getting station names")
            return {sid: f"Station {sid}" for sid in station_ids}
            
        try:
            result = {}
            for station_id in station_ids:
                result[station_id] = self.market_log_parser.get_station_name(station_id)
            return result
        except Exception as e:
            logger.error(f"Error batch getting station names: {e}", exc_info=True)
            return {sid: f"Station {sid}" for sid in station_ids} 