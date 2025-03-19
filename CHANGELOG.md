# Changelog

All notable changes to the EVE Frontier Blueprint Miracle project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-03-15

### Added
- Initial project structure with modular architecture
- Core services implementation:
  - DataLoader service for importing EVE Online data from JSON files
  - SearchService for finding items, blueprints, and materials
  - ProductionService for analyzing manufacturing chains and calculating costs
  - MarketService for retrieving and analyzing market data
  - UserPreferencesService for managing user settings
- Database models implementation:
  - Item models (Category, Group, Item)
  - Blueprint models (Blueprint, BlueprintProduct, BlueprintMaterial, BlueprintActivity, SkillRequirement)
  - Market models (Station, MarketData, MarketOrder, TradingHub, MarketHistory)
- Basic PySide6 UI framework:
  - Main application window with dark theme styling
  - Tab-based interface with placeholders for Item Search, Production Chain, and Market Data
  - Menu bar with File, View, Tools, and Help menus
- Package setup for installation and development
- Comprehensive test suite for services and models

### Changed
- N/A (Initial release)

### Fixed
- N/A (Initial release)

## [0.1.1] - 2025-03-17

### Added
- GitHub repository setup for version control and collaboration
- Creation of 'foundation' branch to preserve initial stable codebase

### Fixed
- Fixed DataLoader's load_items method to correctly map TypeIDs to human-readable names
- Improved batch processing of item data loading for better performance

## [Unreleased]

### Added
- Blueprint Browser tab with search functionality
- Blueprint details display showing products, materials, and activities
- Activity filtering for blueprints
- Comprehensive debug logging for UI component updates
- New filter_blueprints.py script to generate filtered blueprint data
- Support for blueprints_filtered.json as the primary blueprint data source
- Market Data tab with item search functionality
- Price history charts for market data visualization
- Trading hub selection and comparison for market analysis
- Order book visualization for buy and sell orders
- Market statistics display with price trends and volume information
- Enhanced MarketLogParser with improved efficiency and robustness:
  - Order deduplication to prevent duplicates from multiple log files
  - Type ID pre-indexing for faster data access
  - In-memory caching to reduce file parsing operations
  - Batch processing to manage memory usage for large datasets
  - Proper resolution of station names for trading hubs
- "Reload Market Data" button for manually refreshing market data from log files
- Implemented robust error handling in production profit calculation

### Changed
- Updated roadmap to reflect completion of Blueprint Browser tab implementation
- Enhanced UI refresh mechanism for detail panels
- Improved database path resolution with absolute paths
- Modified DataLoader to prioritize filtered blueprint data over raw blueprint data
- Completely revamped search algorithm in SearchService to prioritize exact matches first before falling back to term-based search
- Improved price history chart to only show real market data without synthetic data generation
- Updated station name handling to use generic station IDs without EVE Online-specific naming references
- Enhanced price history chart with clear labeling for data availability status (single data point, real data only)
- Refactored get_market_statistics method in MarketService to return consistent field names and handle edge cases properly
- Updated get_manufacturing_details in ProductionService to better handle items without manufacturing blueprints

### Fixed
- Fixed UI refresh issues in blueprint details panel where changes weren't reflecting when selecting new blueprints
- Resolved missing BlueprintActivity import causing activities tab to not update
- Fixed database path resolution issue by using absolute paths
- Added explicit table clearing and UI update calls to ensure consistent display
- Fixed issue with "phantom" blueprints appearing without names or products in the UI
- Reduced blueprint count from 5,225 to 168 by filtering to only include blueprints with valid product references
- Fixed critical issue in SearchService where multi-word queries like "Steel Plates" were returning incorrect results
- Improved search logic to prioritize exact matches, then starts-with matches, then all-terms matches, before falling back to any-term matches
- Fixed issues with the Production Chain tab not finding specific items due to search algorithm limitations
- Fixed misleading price history charts by removing synthetic data generation and clearly labeling data availability
- Fixed critical issue in Profitability Analyzer Widget where wrong model access patterns caused search failures
- Fixed division by zero errors in market_service.get_market_statistics when calculating spread percentages
- Fixed inconsistent field naming in market_service.get_market_statistics to ensure compatibility with calculate_production_profit
- Fixed error handling in production_service.get_manufacturing_details when no blueprint is found
- Fixed NoneType errors in production_service.get_manufacturing_details when dealing with items without manufacturing blueprints
- Resolved issue with production_service.calculate_production_profit failing to properly evaluate market data
- Fixed issues with ProfitabilityAnalyzerWidget not displaying any profitable items due to service data inconsistencies

### Planned
- Production Chain analysis UI with visualization components
- Market Data analysis UI with price charts
- EVE Online SDE data import functionality
- Blueprint manufacturing optimization tools
- Market order analysis and price tracking 