#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE Frontier Blueprint Miracle - Item Profitability Analyzer

This script analyzes all items with market data and calculates their profitability
if manufactured from blueprints. Results are sorted by profit margin.
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from pathlib import Path
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("profitability_analyzer")

# Ensure parent directory is in path for imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from eve_frontier.models import Item, Blueprint, MarketData
from eve_frontier.services.search_service import SearchService
from eve_frontier.services.market_service import MarketService
from eve_frontier.services.production_service import ProductionService


class ProfitabilityAnalyzer:
    """Analyzer for comparing profitability of different items."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the profitability analyzer.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Set up database connection
        if db_path is None:
            db_path = "eve_frontier.db"
        
        db_path = Path(db_path).resolve()
        logger.info(f"Using database at: {db_path}")
        
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        # Create engine and session
        engine_url = f"sqlite:///{db_path}"
        self.engine = create_engine(engine_url)
        self.session = Session(self.engine)
        
        # Initialize services
        self.search_service = SearchService(self.session)
        self.market_service = MarketService(self.session)
        self.production_service = ProductionService(self.session)
        
        logger.info("Profitability analyzer initialized")
    
    def analyze_all_items(
        self, 
        min_profit_margin: float = 5.0,
        me_level: int = 0,
        include_components: bool = True,
        only_manufacturable: bool = True,
        region_id: Optional[int] = None,
        limit_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Analyze all items with market data for profitability.
        
        Args:
            min_profit_margin: Minimum profit margin (%) to include in results
            me_level: Material Efficiency level to assume for calculations
            include_components: Whether to include component costs in calculations
            only_manufacturable: Only include items that can be manufactured
            region_id: Optional region ID to use for market data
            limit_results: Optional limit on number of results to return
            
        Returns:
            List of item profitability data sorted by profit margin
        """
        logger.info("Starting profitability analysis for all items")
        
        # Get all items with market data
        logger.info("Loading market data")
        market_data = self.market_service._load_unified_market_data()
        if not market_data or 'items' not in market_data:
            logger.error("No market data available")
            return []
        
        # Get list of all item IDs with market data
        item_ids_with_market_data = list(market_data['items'].keys())
        logger.info(f"Found {len(item_ids_with_market_data)} items with market data")
        
        # Initialize results list
        results = []
        skipped_items = 0
        
        # Process each item
        for i, item_id in enumerate(item_ids_with_market_data):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(item_ids_with_market_data)} items")
            
            try:
                # Get item details
                item_id_int = int(item_id)
                item = self.session.query(Item).filter(Item.id == item_id_int).first()
                if not item:
                    logger.warning(f"Item {item_id} not found in database")
                    skipped_items += 1
                    continue
                
                # If only_manufacturable, check if the item has a blueprint
                if only_manufacturable:
                    blueprint = self.production_service._find_manufacturing_blueprint(item_id_int)
                    if not blueprint:
                        skipped_items += 1
                        continue
                
                # Calculate production profit
                profit_data = self.production_service.calculate_production_profit(
                    item_id_int,
                    quantity=1,
                    me_level=me_level,
                    include_components=include_components
                )
                
                # Only include items with profit data
                if not profit_data or 'profit_margin' not in profit_data:
                    skipped_items += 1
                    continue
                
                # Filter by minimum profit margin
                if profit_data['profit_margin'] < min_profit_margin:
                    skipped_items += 1
                    continue
                
                # Add to results
                results.append({
                    'item_id': item_id_int,
                    'item_name': item.name,
                    'production_cost': float(profit_data.get('production_cost', 0)),
                    'market_price': float(profit_data.get('market_price', 0)),
                    'profit': float(profit_data.get('profit', 0)),
                    'profit_margin': float(profit_data.get('profit_margin', 0)),
                    'volume': profit_data.get('daily_volume', 0),
                    'material_efficiency': me_level
                })
            except Exception as e:
                logger.error(f"Error processing item {item_id}: {e}")
                skipped_items += 1
                continue
        
        logger.info(f"Analysis completed. Found {len(results)} profitable items. Skipped {skipped_items} items.")
        
        # Sort results by profit margin
        results.sort(key=lambda x: x['profit_margin'], reverse=True)
        
        # Limit results if specified
        if limit_results:
            results = results[:limit_results]
        
        return results
    
    def analyze_specific_item(
        self, 
        item_id: int,
        me_level: int = 0,
        include_components: bool = True
    ) -> Dict:
        """
        Perform detailed analysis of a specific item.
        
        Args:
            item_id: ID of the item to analyze
            me_level: Material Efficiency level to assume
            include_components: Whether to include component costs
            
        Returns:
            Dictionary with detailed profitability analysis
        """
        logger.info(f"Analyzing item {item_id}")
        
        # Get item details
        item = self.session.query(Item).filter(Item.id == item_id).first()
        if not item:
            logger.error(f"Item {item_id} not found")
            return {}
        
        # Get manufacturing details
        manufacturing_details = self.production_service.get_manufacturing_details(
            item_id,
            quantity=1,
            me_level=me_level,
            max_depth=10
        )
        
        if not manufacturing_details:
            logger.error(f"No manufacturing details found for item {item_id}")
            return {}
        
        # Calculate profit data
        profit_data = self.production_service.calculate_production_profit(
            item_id,
            quantity=1,
            me_level=me_level,
            include_components=include_components
        )
        
        # Return combined data
        result = {
            'item_id': item_id,
            'item_name': item.name,
            'production_cost': float(profit_data.get('production_cost', 0)),
            'market_price': float(profit_data.get('market_price', 0)),
            'profit': float(profit_data.get('profit', 0)),
            'profit_margin': float(profit_data.get('profit_margin', 0)),
            'volume': profit_data.get('daily_volume', 0),
            'material_efficiency': me_level,
            'manufacturing_details': manufacturing_details.to_dict() if manufacturing_details else {}
        }
        
        return result
    
    def export_results_to_csv(self, results: List[Dict], output_file: str):
        """
        Export analysis results to CSV file.
        
        Args:
            results: Analysis results to export
            output_file: Path to output CSV file
        """
        if not results:
            logger.warning("No results to export")
            return
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV fields
        fields = [
            'item_id', 'item_name', 'production_cost', 'market_price', 
            'profit', 'profit_margin', 'volume', 'material_efficiency'
        ]
        
        try:
            # Write CSV file
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for item in results:
                    # Only write fields that are in our field list
                    row = {field: item.get(field, '') for field in fields}
                    writer.writerow(row)
            
            logger.info(f"Results exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")


def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze profitability of manufacturable items')
    parser.add_argument('--db-path', type=str, help='Path to the database file')
    parser.add_argument('--min-margin', type=float, default=5.0, help='Minimum profit margin percentage')
    parser.add_argument('--me-level', type=int, default=0, help='Material efficiency level')
    parser.add_argument('--item-id', type=int, help='Analyze a specific item by ID')
    parser.add_argument('--output', type=str, default='profitability_analysis.csv', help='Output CSV file path')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    parser.add_argument('--include-all', action='store_true', help='Include non-manufacturable items')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = ProfitabilityAnalyzer(db_path=args.db_path)
        
        if args.item_id:
            # Analyze specific item
            result = analyzer.analyze_specific_item(
                item_id=args.item_id,
                me_level=args.me_level
            )
            
            # Print detailed result
            print(f"\nDetailed analysis for item {result.get('item_name', 'Unknown')} (ID: {args.item_id}):")
            print(f"Production Cost: {result.get('production_cost', 'N/A'):,.2f} ISK")
            print(f"Market Price: {result.get('market_price', 'N/A'):,.2f} ISK")
            print(f"Profit: {result.get('profit', 'N/A'):,.2f} ISK")
            print(f"Profit Margin: {result.get('profit_margin', 'N/A'):.2f}%")
            print(f"Daily Volume: {result.get('volume', 'N/A'):,}")
            
            # Save detailed manufacturing data to a separate file
            detailed_output = f"detailed_analysis_{args.item_id}.txt"
            with open(detailed_output, 'w') as f:
                f.write(f"Detailed analysis for {result.get('item_name', 'Unknown')} (ID: {args.item_id})\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write manufacturing details
                if 'manufacturing_details' in result and result['manufacturing_details']:
                    import json
                    f.write(json.dumps(result['manufacturing_details'], indent=2))
                else:
                    f.write("No manufacturing details available.")
            
            print(f"\nDetailed manufacturing information saved to {detailed_output}")
            
        else:
            # Analyze all items
            results = analyzer.analyze_all_items(
                min_profit_margin=args.min_margin,
                me_level=args.me_level,
                only_manufacturable=not args.include_all,
                limit_results=args.limit
            )
            
            # Export results
            analyzer.export_results_to_csv(results, args.output)
            
            # Print top 10 most profitable items
            if results:
                print("\nTop 10 Most Profitable Items:")
                print("-" * 80)
                print(f"{'Item Name':<40} {'Profit Margin':<15} {'Profit':<15} {'Production Cost':<15}")
                print("-" * 80)
                
                for i, item in enumerate(results[:10]):
                    print(f"{item['item_name']:<40} {item['profit_margin']:<15.2f}% {item['profit']:<15,.2f} {item['production_cost']:<15,.2f}")
                
                print("-" * 80)
                print(f"Total profitable items found: {len(results)}")
                print(f"Full results saved to: {args.output}")
            else:
                print("No profitable items found matching criteria.")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 