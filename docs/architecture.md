# EVE Frontier Blueprint Miracle - Architecture

## Overview

EVE Frontier Blueprint Miracle is a GUI application for analyzing EVE Frontier blueprints and production chains. It provides tools for searching items, analyzing manufacturing costs, and optimizing production.

## Architecture

The application follows a Model-View-Controller (MVC) architecture with modular components:

### Directory Structure

```
eve_frontier_blueprint/
├── config/                # Configuration files and settings
├── data/                  # Data files (JSON)
│   ├── json/              # Original game data files
│   └── refined_market_data/ # Processed market data
├── logs/                  # Application logs
├── src/
│   ├── core/              # Core business logic
│   │   ├── data_loader.py # Data loading from JSON files
│   │   ├── data_mapper.py # Mapping relationships between data
│   │   ├── blueprint.py   # Blueprint analysis
│   │   └── production.py  # Production chain analysis
│   ├── models/            # Data models/classes
│   │   ├── item.py        # Item model
│   │   ├── blueprint.py   # Blueprint model
│   │   ├── market.py      # Market data model
│   │   └── settings.py    # User settings model
│   ├── services/          # Service layer
│   │   ├── search.py      # Item search functionality
│   │   ├── market.py      # Market analysis services
│   │   ├── export.py      # Data export services
│   │   └── history.py     # Search history management
│   ├── ui/                # UI components
│   │   ├── main_window.py # Main application window
│   │   ├── tabs/          # Individual tab UIs
│   │   ├── dialogs/       # Dialog components
│   │   └── widgets/       # Reusable UI widgets
│   └── utils/             # Utility functions
│       ├── logger.py      # Logging setup
│       └── helpers.py     # Helper utilities
├── tests/                 # Unit and integration tests
├── main.py                # Application entry point
└── README.md              # Documentation
```

### Key Components

#### Data Layer

- **Data Loader**: Loads and parses JSON data files
- **Data Mapper**: Maps relationships between different data types
- **Models**: Represents items, blueprints, and other game entities

#### Business Logic Layer

- **Blueprint Analyzer**: Analyzes blueprint manufacturing requirements
- **Production Chain Analyzer**: Calculates full production chains
- **Market Analyzer**: Analyzes market prices and costs

#### UI Layer

- **Main Window**: Primary application window with tabs
- **Item Search Tab**: Interface for searching and displaying items
- **Production Chain Tab**: Interface for analyzing production chains
- **Market Analysis Tab**: Interface for market data and pricing

#### Utility Layer

- **Logger**: Centralized logging system
- **Error Handling**: Consistent error handling and reporting

## Data Flow

1. Application loads data from JSON files
2. User interacts with UI to search for items or analyze blueprints
3. Business logic processes the requests and returns results
4. UI displays the results to the user
5. User can export data or save custom settings

## Design Principles

- **Modularity**: Components are self-contained and have clear interfaces
- **Separation of Concerns**: UI, business logic, and data access are separated
- **Error Handling**: Consistent error handling throughout the application
- **Logging**: Comprehensive logging for debugging and troubleshooting
- **Testability**: Components are designed to be easily testable
