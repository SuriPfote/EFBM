# EVE Frontier Blueprint Miracle

A tool for analyzing EVE Online blueprints and optimizing production chains.

## Overview

EVE Frontier Blueprint Miracle is a desktop application that helps EVE Online players analyze blueprints, calculate production costs, and optimize manufacturing chains. The application provides a user-friendly interface for searching items, analyzing production requirements, and making informed manufacturing decisions.

## Current State

The application is currently in version 0.1.0, with the following components implemented:

- Core service layer with data loading, searching, production chain analysis, and market data processing
- Database models for items, blueprints, and market data
- Basic UI framework with placeholder tabs for the main functionality
- Comprehensive test suite for the service layer
- GitHub integration with foundation branch to preserve baseline implementation

See the [CHANGELOG.md](CHANGELOG.md) for detailed information about project history.

## Features

- **Item Search**: Search for items by name with category filtering and autocomplete
- **Blueprint Analysis**: View detailed information about blueprints, including materials and manufacturing time
- **Production Chain Calculation**: Calculate complete production chains with material efficiency consideration
- **Cost Estimation**: Estimate production costs based on market or custom prices
- **Manufacturing Optimization**: Find the optimal material efficiency level for production
- **Market Data Integration**: View and analyze market data from EVE Online logs
- **Searchable Dropdowns**: Intelligent search capabilities in input fields

## Installation

### Prerequisites

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

### Setup

1. Clone the repository:

   ```
   git clone https://github.com/SuriPfote/EFBM.git
   cd EFBM
   ```

2. Install in development mode:

   ```
   pip install -e .
   ```

3. Run the application:

   ```
   python run.py
   ```

## Development

### GitHub Repository

The project is hosted on GitHub at [https://github.com/SuriPfote/EFBM](https://github.com/SuriPfote/EFBM).

Key branches:
- `master`: Main development branch
- `foundation`: Stable baseline implementation with core functionality

### Project Structure

```
eve_frontier/
├── main.py                           # Application entry point
├── config.py                         # Configuration settings
├── models/                           # SQLAlchemy models
│   ├── base.py                       # Base model configuration
│   ├── item.py                       # Item types, groups, categories
│   ├── blueprint.py                  # Blueprint data
│   └── market.py                     # Market data
├── services/                         # Business logic
│   ├── data_loader.py                # Data import from JSON
│   ├── search_service.py             # Item search functionality
│   ├── production_service.py         # Production chain analysis
│   ├── market_service.py             # Market data analysis
│   └── user_preferences.py           # User settings management
├── ui/                               # PySide6 UI components
│   ├── main_window.py                # Main application window
│   └── tabs/                         # Tab implementations
└── utils/                            # Utility functions
```

### Technology Stack

- **PySide6**: Modern UI framework based on Qt
- **SQLAlchemy**: Object-relational mapper for database interactions
- **Pandas**: Data processing and analysis
- **Matplotlib**: Data visualization
- **NumPy**: Numerical computing

For details, see [tech_stack.md](tech_stack.md).

### Running Tests

```
python test_models.py
python test_services.py
```

## Documentation

- [Architecture](docs/architecture.md): High-level application architecture
- [Data Structure](docs/data_structure.md): Database model design
- [Features](docs/features.md): Detailed feature descriptions
- [Implementation Plan](docs/implementation_plan.md): Development roadmap
- [Troubleshooting](docs/troubleshooting.md): Common issues and solutions

## Contributing

Contributions are welcome! Here's how to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

### Git Workflow

The project follows a feature branch workflow:
- Create feature branches from `master`
- Submit pull requests to merge into `master`
- Tag significant releases with version numbers
- The `foundation` branch preserves the initial baseline implementation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- EVE Online and all related trademarks are the property of CCP Games
- This application is for educational and personal use only
