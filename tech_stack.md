# EVE Frontier Blueprint Miracle - Technology Stack

## Overview
This document outlines the selected technology stack for rebuilding the EVE Frontier Blueprint Miracle application. We're focusing on leveraging established libraries and frameworks to minimize custom code and accelerate development.

## Core Technologies

### Frontend/GUI
- **PySide6 (Qt for Python)**
  - Modern, feature-rich UI framework
  - Cross-platform compatibility
  - Rich widget ecosystem
  - Qt Designer for visual UI development
  - Built-in support for model-view architecture
  - Stylesheet support for customization

### Data Processing
- **Pandas**
  - DataFrame structure for item and blueprint data
  - Efficient filtering, grouping, and aggregation
  - Easy JSON data import/export
  - Integration with visualization libraries

### Data Storage
- **SQLAlchemy with SQLite**
  - ORM for object-oriented data access
  - Relationship management between entities
  - Efficient querying of large datasets
  - No separate database server required
  - Support for complex queries

### Production Chain Analysis
- **NetworkX**
  - Graph representation of production dependencies
  - Path finding and traversal algorithms
  - Visualization of production chains
  - Support for directed graphs (perfect for dependencies)

### Numerical Computing
- **NumPy**
  - Efficient numerical calculations
  - Support for complex math operations
  - Used for material efficiency and cost optimization

### Visualization
- **Matplotlib/Plotly**
  - Static and interactive visualizations
  - Market trend charts
  - Cost breakdown visualizations
  - Production chain diagrams

### Configuration
- **Pydantic**
  - Type-safe configuration with validation
  - Data models with validation
  - Settings management

## Directory Structure

```
eve_frontier/
├── main.py                           # Application entry point
├── models/                           # SQLAlchemy/Pydantic models
│   ├── item.py                       # Item types
│   ├── blueprint.py                  # Blueprint data
│   ├── market_data.py                # Market pricing
│   └── settings.py                   # User settings
├── services/                         # Business logic
│   ├── data_loader.py                # JSON data import
│   ├── blueprint_analyzer.py         # Production analysis
│   ├── market_analyzer.py            # Price analysis
│   └── search_service.py             # Item search functionality
├── ui/                               # PySide6 UI components
│   ├── main_window.py                # Main application window
│   ├── tabs/
│   │   ├── search_tab.py             # Item search interface
│   │   ├── production_tab.py         # Production analysis
│   │   └── market_tab.py             # Market data analysis
│   └── widgets/
│       ├── searchable_combobox.py    # Custom search widget
│       └── production_tree.py        # Production chain visualization
├── utils/                            # Utility functions
│   ├── logger.py                     # Logging setup
│   └── helpers.py                    # Helper functions
└── config.py                         # Pydantic configuration
```

## Implementation Notes

### Data Import
- Use Pandas to read and preprocess JSON game data files
- Map relationships between items, blueprints, and categories
- Create SQLAlchemy models matching the data structure

### UI Development
- Create UI layouts with Qt Designer (.ui files)
- Use PySide6's model-view architecture for data tables and trees
- Implement custom widgets (like searchable combobox) as reusable components

### Production Chain Analysis
- Represent production chains as directed graphs in NetworkX
- Each node is an item, each edge represents a manufacturing requirement
- Calculate optimal material efficiency using NumPy operations

### Market Data Processing
- Parse market logs using Pandas
- Store processed market data in SQLite database
- Implement price calculation and analysis in market_analyzer service

## Dependencies

```
pyside6==6.8.2.1
pandas==2.2.3
sqlalchemy==2.0.39
networkx==3.4.2
numpy==2.2.3
matplotlib==3.10.0
plotly==6.0.0
pydantic==2.10.6
```

## Development Tools
- **Visual Studio Code** with Python extension
- **Qt Designer** for UI layout design
- **Git** for version control 