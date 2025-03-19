"""
EVE Frontier Blueprint Miracle - UI Package

This package contains the user interface components for the EVE Frontier Blueprint Miracle application.
The UI is built using PySide6, providing a modern, responsive interface for the application.

Main components:
- MainWindow: The main application window
- Various UI tabs for different functionality
"""

from .main_window import MainWindow
from eve_frontier.ui.tabs.blueprint_browser import BlueprintBrowserTab
from eve_frontier.ui.tabs.production_chain import ProductionChainTab
from eve_frontier.ui.tabs.market_data import MarketDataTab

# Import custom widgets
from eve_frontier.ui.widgets.profitability_analyzer_widget import ProfitabilityAnalyzerWidget

__all__ = [
    'MainWindow',
    'BlueprintBrowserTab',
    'ProductionChainTab',
    'MarketDataTab',
    'ProfitabilityAnalyzerWidget'
] 