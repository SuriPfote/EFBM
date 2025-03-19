"""
Market Log Parser for EVE Frontier Blueprint Miracle.

This module provides functionality to parse EVE Online market log files and convert them
into structured data that can be used by the MarketService.
"""

import os
import csv
import json
import logging
import datetime
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Set, Generator
from collections import defaultdict

logger = logging.getLogger(__name__)

class MarketLogParser:
    """Parser for EVE Online market log files."""
    
    def __init__(self, log_directory: str, cache_directory: Optional[str] = None):
        """
        Initialize the MarketLogParser.
        
        Args:
            log_directory: Directory containing market log files
            cache_directory: Optional directory for caching processed data
        """
        self.log_directory = Path(log_directory)
        self.cache_directory = Path(cache_directory) if cache_directory else None
        
        # Ensure directories exist
        if not self.log_directory.exists():
            logger.warning(f"Log directory does not exist: {self.log_directory}")
        
        if self.cache_directory and not self.cache_directory.exists():
            logger.info(f"Creating cache directory: {self.cache_directory}")
            self.cache_directory.mkdir(parents=True, exist_ok=True)
        
        # Create indexes for faster lookups
        self._type_id_to_files = defaultdict(list)  # Map type_ids to files containing orders for that type
        self._file_cache = {}  # Cache for parsed files to avoid re-parsing
    
    def get_available_items(self) -> List[Dict[str, Any]]:
        """
        Get a list of items for which market data is available.
        
        Returns:
            List of dictionaries containing item information
        """
        items = []
        seen_type_ids = set()
        
        for file_path in self.log_directory.glob("*.txt"):
            try:
                # Parse the filename to extract item info using regex
                # Assume format like: [Region]-[ItemName]-[Date].txt or L4.Q2.CC-Steel Plates-2025.03.12 225305.txt
                # The important part is extracting the item name which is between the first and last hyphens
                parts = file_path.stem.split("-")
                if len(parts) < 2:
                    continue
                
                # Extract item name (may contain hyphens)
                if len(parts) > 2:
                    item_name = "-".join(parts[1:-1])
                else:
                    item_name = parts[1]
                
                # Read the first few rows to find type IDs
                type_ids = self._extract_type_ids_from_file(file_path, limit=5)
                
                for type_id in type_ids:
                    if type_id in seen_type_ids:
                        continue
                    
                    seen_type_ids.add(type_id)
                    
                    # Create an index entry for faster lookups
                    self._type_id_to_files[type_id].append(file_path)
                    
                    items.append({
                        'name': item_name.strip(),
                        'type_id': type_id,
                        'log_files': [str(file_path.name)]
                    })
            
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        logger.info(f"Found {len(items)} unique items in market logs")
        return items
    
    def _extract_type_ids_from_file(self, file_path: Path, limit: int = 5) -> Set[int]:
        """
        Extract type IDs from the first few rows of a file.
        
        Args:
            file_path: Path to the log file
            limit: Maximum number of rows to check
            
        Returns:
            Set of type IDs found in the file
        """
        type_ids = set()
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    
                    type_id = int(row.get('typeID', 0))
                    if type_id > 0:
                        type_ids.add(type_id)
        except Exception as e:
            logger.warning(f"Error extracting type IDs from {file_path}: {e}")
        
        return type_ids
    
    def parse_log_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse a single market log file.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of dictionaries containing order data
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        
        # Check if we already parsed this file
        if str(file_path) in self._file_cache:
            logger.debug(f"Using cached data for {file_path}")
            return self._file_cache[str(file_path)]
        
        logger.debug(f"Parsing market log file: {file_path}")
        
        orders = []
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Convert values to appropriate types
                        order = {
                            'price': float(row.get('price', 0)),
                            'volume_remaining': int(float(row.get('volRemaining', 0))),
                            'type_id': int(row.get('typeID', 0)),
                            'range': int(row.get('range', 0)),
                            'order_id': int(row.get('orderID', 0)),
                            'volume_entered': int(float(row.get('volEntered', 0))),
                            'min_volume': int(float(row.get('minVolume', 0))),
                            'is_buy_order': row.get('bid', 'False').lower() == 'true',
                            'issue_date': row.get('issueDate', ''),
                            'duration': int(row.get('duration', 0)),
                            'station_id': int(row.get('stationID', 0)),
                            'region_id': int(row.get('regionID', 0)),
                            'solar_system_id': int(row.get('solarSystemID', 0)),
                            'jumps': int(row.get('jumps', 0)) if row.get('jumps', '2147483647') != '2147483647' else None
                        }
                        orders.append(order)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing row in {file_path}: {e}")
                        continue
            
            # Cache the parsed file
            self._file_cache[str(file_path)] = orders
            
            logger.debug(f"Parsed {len(orders)} orders from {file_path}")
            return orders
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []
    
    def parse_logs_for_item(self, item_name: str) -> List[Dict[str, Any]]:
        """
        Parse all market logs for a specific item.
        
        Args:
            item_name: Name of the item
            
        Returns:
            List of dictionaries containing order data
        """
        logger.info(f"Parsing market logs for item: {item_name}")
        
        # Find all log files for this item
        log_files = list(self.log_directory.glob(f"*-{item_name}-*.txt"))
        
        # If no exact match, try a more flexible search
        if not log_files:
            log_files = [f for f in self.log_directory.glob("*.txt") 
                        if item_name.lower() in f.stem.lower()]
        
        if not log_files:
            logger.warning(f"No market log files found for item: {item_name}")
            return []
        
        # Parse each log file and deduplicate orders by order_id
        order_map = {}  # Use a dict to deduplicate orders
        for file_path in log_files:
            orders = self.parse_log_file(file_path)
            for order in orders:
                order_id = order['order_id']
                # Keep the most recent version of each order (based on issue_date)
                if (order_id not in order_map or 
                    order['issue_date'] > order_map[order_id]['issue_date']):
                    order_map[order_id] = order
        
        # Convert back to a list
        all_orders = list(order_map.values())
        
        logger.info(f"Found {len(all_orders)} unique orders for {item_name} across {len(log_files)} files")
        return all_orders
    
    def parse_logs_for_type_id(self, type_id: int) -> List[Dict[str, Any]]:
        """
        Parse all market logs for a specific item type ID.
        
        Args:
            type_id: Type ID of the item
            
        Returns:
            List of dictionaries containing order data
        """
        logger.info(f"Parsing market logs for type ID: {type_id}")
        
        # Use the pre-indexed file list if available
        if type_id in self._type_id_to_files and self._type_id_to_files[type_id]:
            log_files = self._type_id_to_files[type_id]
        else:
            # Fallback: scan all files
            log_files = []
            for file_path in self.log_directory.glob("*.txt"):
                # Check if this file contains the type ID
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    found = False
                    for row in reader:
                        if int(row.get('typeID', 0)) == type_id:
                            found = True
                            break
                
                if found:
                    log_files.append(file_path)
                    # Add to index for future reference
                    self._type_id_to_files[type_id].append(file_path)
        
        # Parse and deduplicate orders
        order_map = {}
        for file_path in log_files:
            orders = self.parse_log_file(file_path)
            # Filter to just the orders with this type ID
            for order in (o for o in orders if o['type_id'] == type_id):
                order_id = order['order_id']
                # Keep the most recent version of each order
                if (order_id not in order_map or 
                    order['issue_date'] > order_map[order_id]['issue_date']):
                    order_map[order_id] = order
        
        # Convert back to a list
        all_orders = list(order_map.values())
        
        logger.info(f"Found {len(all_orders)} unique orders for type ID {type_id}")
        return all_orders
    
    def _get_market_log_files(self) -> List[Path]:
        """
        Get a list of all market log files in the log directory.
        
        Returns:
            List of Path objects pointing to market log files
        """
        return list(self.log_directory.glob("*.txt"))
    
    def save_cached_data(self, data: Dict[str, Any], cache_name: str) -> bool:
        """
        Save data to a JSON cache file.
        
        Args:
            data: The data to cache
            cache_name: Name for the cache file
            
        Returns:
            True if successful, False otherwise
        """
        return self.cache_parsed_data(data, cache_name)
    
    def get_trading_hubs(self) -> List[Dict[str, Any]]:
        """
        Get a list of trading hubs (stations) found in the market logs.
        
        Returns:
            List of trading hub dictionaries with id, name, and order_count
        """
        logger.info("Extracting trading hubs from market logs")
        
        try:
            # Try to load from cache first
            cached_data = self.load_cached_data("unified_market_data")
            
            if cached_data and 'trading_hubs' in cached_data and cached_data['trading_hubs']:
                logger.info(f"Loaded {len(cached_data['trading_hubs'])} trading hubs from cache")
                return cached_data['trading_hubs']
            
            # If not in cache, extract from market logs
            # 1. Collect all station IDs from the market logs
            station_ids = set()
            station_order_counts = defaultdict(int)
            
            # Iterate through all log files to find station IDs
            log_files = self._get_market_log_files()
            logger.info(f"Scanning {len(log_files)} market log files for station IDs")
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Skip header
                        header_line = f.readline().strip()
                        header = next(csv.reader([header_line]))
                        
                        # Find station ID column index
                        station_id_index = None
                        for i, col in enumerate(header):
                            if col.lower() == 'stationid':
                                station_id_index = i
                                break
                        
                        if station_id_index is None:
                            logger.warning(f"No stationID column found in {log_file}")
                            continue
                        
                        # Read the CSV data
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) > station_id_index:
                                try:
                                    station_id = int(row[station_id_index])
                                    station_ids.add(station_id)
                                    station_order_counts[station_id] += 1
                                except (ValueError, IndexError) as e:
                                    logger.debug(f"Error parsing station ID in row: {e}")
                                    pass
                except Exception as e:
                    logger.warning(f"Error reading station IDs from {log_file}: {e}")
                    continue
            
            logger.info(f"Found {len(station_ids)} unique station IDs in market logs")
            for station_id in list(station_ids)[:10]:
                logger.debug(f"Station {station_id}: {station_order_counts[station_id]} orders")
            
            # 2. Create trading hub entries
            trading_hubs = []
            
            for station_id in station_ids:
                # Use a placeholder name based on the station ID
                # In a real implementation, you would look up the station name from EVE's static data
                trading_hub = {
                    'id': station_id,
                    'name': self.get_station_name(station_id),
                    'order_count': station_order_counts[station_id],
                    'solar_system_id': 0,  # Unknown
                    'region_id': 0,        # Unknown
                }
                trading_hubs.append(trading_hub)
            
            # Sort by order count (descending)
            trading_hubs.sort(key=lambda h: h['order_count'], reverse=True)
            
            # Cache the data for future use
            if cached_data and 'items' in cached_data:
                cached_data['trading_hubs'] = trading_hubs
                self.cache_parsed_data(cached_data, "unified_market_data")
                logger.info(f"Cached {len(trading_hubs)} trading hubs")
            
            return trading_hubs
        
        except Exception as e:
            logger.error(f"Error getting trading hubs: {e}", exc_info=True)
            return []
    
    def cache_parsed_data(self, data: Dict[str, Any], cache_name: str) -> bool:
        """
        Cache parsed data to a JSON file.
        
        Args:
            data: Data to cache
            cache_name: Name for the cache file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.cache_directory:
            return False
        
        try:
            cache_path = self.cache_directory / f"{cache_name}.json"
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Cached data to {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching data: {e}")
            return False
    
    def load_cached_data(self, cache_name: str) -> Optional[Dict[str, Any]]:
        """
        Load cached data from a JSON file.
        
        Args:
            cache_name: Name of the cache file
            
        Returns:
            Cached data or None if no cache exists or error occurs
        """
        if not self.cache_directory:
            return None
        
        cache_path = self.cache_directory / f"{cache_name}.json"
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded cached data from {cache_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading cached data: {e}")
            return None
    
    def _process_item_batch(self, items_batch: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Process a batch of items to generate their market data.
        
        Args:
            items_batch: List of item dictionaries to process
            
        Returns:
            Dictionary of processed item data
        """
        result = {}
        
        for item in items_batch:
            item_name = item['name']
            type_id = item['type_id']
            str_type_id = str(type_id)
            
            # Parse logs for this item
            orders = self.parse_logs_for_type_id(type_id)
            
            # Group orders by whether they're buy or sell orders
            buy_orders = [o for o in orders if o['is_buy_order']]
            sell_orders = [o for o in orders if not o['is_buy_order']]
            
            # Sort orders by price (buy: highest first, sell: lowest first)
            buy_orders = sorted(buy_orders, key=lambda o: o['price'], reverse=True)
            sell_orders = sorted(sell_orders, key=lambda o: o['price'])
            
            # Calculate price statistics
            min_sell = sell_orders[0]['price'] if sell_orders else None
            max_buy = buy_orders[0]['price'] if buy_orders else None
            
            # Add to result
            result[str_type_id] = {
                'name': item_name,
                'type_id': type_id,
                'statistics': {
                    'min_sell_price': min_sell,
                    'max_buy_price': max_buy,
                    'spread': (min_sell - max_buy) if min_sell and max_buy else None,
                    'sell_order_count': len(sell_orders),
                    'buy_order_count': len(buy_orders),
                    'total_sell_volume': sum(o['volume_remaining'] for o in sell_orders),
                    'total_buy_volume': sum(o['volume_remaining'] for o in buy_orders)
                },
                'buy_orders': buy_orders[:20],  # Limit to top 20
                'sell_orders': sell_orders[:20]  # Limit to top 20
            }
        
        return result
    
    def parse_all_logs(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Parse all market logs and create a unified data structure.
        
        Args:
            batch_size: Number of items to process in each batch
            
        Returns:
            Dictionary containing structured market data
        """
        logger.info("Parsing all market logs")
        
        # Check if we have cached data
        cached_data = self.load_cached_data("unified_market_data")
        if cached_data:
            return cached_data
        
        # Get list of items
        items = self.get_available_items()
        
        # Get trading hubs
        trading_hubs = self.get_trading_hubs()
        
        # Initialize market data structure
        market_data = {
            'metadata': {
                'generated_at': datetime.datetime.now().isoformat(),
                'item_count': len(items),
                'trading_hub_count': len(trading_hubs)
            },
            'items': {},
            'trading_hubs': trading_hubs
        }
        
        # Process items in batches to manage memory usage
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{len(items)//batch_size + 1} ({len(batch)} items)")
            
            # Process the batch
            batch_result = self._process_item_batch(batch)
            
            # Add to the main market data
            market_data['items'].update(batch_result)
            
            # Optionally cache intermediate results
            if i > 0 and i % 100 == 0:
                self.cache_parsed_data(market_data, f"unified_market_data_intermediate_{i}")
        
        # Cache the final parsed data
        self.cache_parsed_data(market_data, "unified_market_data")
        
        logger.info(f"Parsed market data for {len(market_data['items'])} items")
        return market_data
    
    def get_station_name(self, station_id: int) -> str:
        """
        Get the name of a station from its ID.
        
        For EVE Frontier, we use a simple naming pattern based on station ID
        since we don't have access to external station name mappings.
        
        Args:
            station_id: Station ID
            
        Returns:
            Station name
        """
        # Use a simple naming scheme based on the station ID
        return f"Station {station_id}"
        
    def clear_cache(self):
        """Clear the in-memory file cache to free up memory."""
        self._file_cache.clear()
        logger.info("In-memory cache cleared")

    def clear_cache_and_reload(self) -> Dict[str, Any]:
        """
        Clear the cache and force reloading all market data from log files.
        
        Returns:
            The newly parsed and cached market data
        """
        logger.info("Clearing cache and reloading market data from log files")
        
        # Delete the cache file if it exists
        cache_file = os.path.join(self.cache_directory, "unified_market_data.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                logger.info(f"Deleted cache file: {cache_file}")
            except Exception as e:
                logger.error(f"Failed to delete cache file: {e}", exc_info=True)
        
        # Clear in-memory cache
        self._file_cache.clear()
        
        # Parse all logs and create a new cache
        logger.info("Parsing all logs to generate new cache")
        unified_data = self.parse_all_logs()
        
        if unified_data:
            # Get trading hubs to ensure they're included in the cache
            logger.info("Extracting trading hubs for cache")
            # Force extraction of trading hubs directly from log files
            station_ids = set()
            station_order_counts = defaultdict(int)
            
            log_files = self._get_market_log_files()
            logger.info(f"Scanning {len(log_files)} market log files for station IDs")
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Skip header
                        header_line = f.readline().strip()
                        header = next(csv.reader([header_line]))
                        
                        # Find station ID column index
                        station_id_index = None
                        for i, col in enumerate(header):
                            if col.lower() == 'stationid':
                                station_id_index = i
                                break
                        
                        if station_id_index is None:
                            continue
                        
                        # Read the CSV data
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) > station_id_index:
                                try:
                                    station_id = int(row[station_id_index])
                                    station_ids.add(station_id)
                                    station_order_counts[station_id] += 1
                                except (ValueError, IndexError):
                                    pass
                except Exception as e:
                    logger.warning(f"Error reading station IDs from {log_file}: {e}")
                    continue
            
            logger.info(f"Found {len(station_ids)} unique station IDs in market logs")
            
            # Create trading hub entries
            trading_hubs = []
            for station_id in station_ids:
                trading_hub = {
                    'id': station_id,
                    'name': self.get_station_name(station_id),
                    'order_count': station_order_counts[station_id],
                    'solar_system_id': 0,
                    'region_id': 0,
                }
                trading_hubs.append(trading_hub)
            
            # Sort by order count (descending)
            trading_hubs.sort(key=lambda h: h['order_count'], reverse=True)
            
            # Add trading hubs to unified data
            unified_data['trading_hubs'] = trading_hubs
            
            # Cache the updated data
            self.cache_parsed_data(unified_data, "unified_market_data")
            logger.info(f"Created new cache with {len(unified_data.get('items', {}))} items and {len(trading_hubs)} trading hubs")
        else:
            logger.error("Failed to parse market logs")
        
        return unified_data 