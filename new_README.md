# EVE Frontier Blueprint Miracle

A desktop application for analyzing EVE Online blueprints, calculating production costs, and optimizing manufacturing chains.

## Overview

EVE Frontier Blueprint Miracle helps EVE Online players analyze blueprints, calculate production costs, and optimize manufacturing chains through a user-friendly interface for searching items, analyzing production requirements, and making informed manufacturing decisions.

## Features

- **Item Search**: Search for items by name with filtering and autocomplete
- **Blueprint Analysis**: View detailed information about blueprints, including materials and manufacturing time
- **Production Chain Calculation**: Calculate complete production chains with material efficiency consideration
- **Cost Estimation**: Estimate production costs based on market or custom prices
- **Manufacturing Optimization**: Find the optimal material efficiency level for production
- **Market Data Integration**: View and analyze market data from EVE Online logs

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/blueprint-miracle.git
   cd blueprint-miracle
   ```

2. Create a virtual environment (recommended):
   ```
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up data files:
   - Copy your EVE Online data files to the `data/json` directory:
     - types_filtered.json
     - blueprints.json
     - groups.json
     - categories.json
   - Copy your market logs to `data/csv/Marketlogs` directory

5. Run the application:
   ```
   python main.py
   ```

## Development

### Development Setup

1. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```
   pre-commit install
   ```

### Running Tests

```
pytest
```

### Code Formatting

```
black .
isort .
```

### Type Checking

```
mypy .
```

## Project Structure

The project follows a modular architecture with clear separation of concerns:

```
eve_frontier/
├── main.py                           # Application entry point
├── models/                           # Data models
├── services/                         # Business logic
├── ui/                               # User interface
│   ├── tabs/                         # Tab components
│   └── widgets/                      # Custom widgets
└── utils/                            # Utility functions
```

For more detailed information about the technology stack and implementation details, see [tech_stack.md](tech_stack.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- EVE Online and all related trademarks are the property of CCP Games
- This application is for educational and personal use only 