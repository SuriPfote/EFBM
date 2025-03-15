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

## [Unreleased]

### Planned
- Item Search UI implementation with searchable comboboxes
- Production Chain analysis UI with visualization components
- Market Data analysis UI with price charts
- EVE Online SDE data import functionality
- Blueprint manufacturing optimization tools
- Market order analysis and price tracking 