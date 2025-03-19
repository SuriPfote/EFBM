"""
Market Data Tab for EVE Frontier Blueprint Miracle.

This module defines the Market Data tab which allows users to view and analyze market data
for items, including price history, trading hub comparison, and order book visualization.

Implementation features:
- Thread-safe background data loading with proper resource management to prevent thread leaks
- Cancellation mechanisms for safely terminating background operations
- Visual feedback during long operations through semi-transparent overlays
- Model-View architecture for displaying order book data
- Tab change event handling to ensure proper resource cleanup
"""

import logging
from typing import List, Optional, Dict, Any
import datetime
import random
from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, QTabWidget,
    QPushButton, QGroupBox, QFormLayout, QSplitter, QHeaderView,
    QCheckBox, QScrollArea, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QFrame, QSizePolicy, QDateEdit, QApplication, QMessageBox,
    QTableView
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QDate, QObject, QThread, QTimer, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont, QIcon, QPainter, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis

from sqlalchemy.orm import Session

from eve_frontier.models import Item, TradingHub, MarketData, MarketHistory
from eve_frontier.services.search_service import SearchService
from eve_frontier.services.market_service import MarketService
from eve_frontier.ui.widgets.profitability_analyzer_widget import ProfitabilityAnalyzerWidget

logger = logging.getLogger(__name__)

# Table column constants
RESULTS_COLUMNS = ["Item", "Category"]
HUB_COMPARISON_COLUMNS = ["Trading Hub", "Sell Price", "Buy Price", "Spread"]
ORDER_COLUMNS = ["Price", "Quantity", "Location", "Updated"]


class DataLoader(QThread):
    """
    Background thread for loading data without freezing the UI.
    
    Features:
    - Safe cancellation mechanism using a flag instead of direct termination
    - Proper signal handling for communication with the main thread
    - Status tracking to monitor active state
    """
    
    # Define signals for communication with the main thread
    finished = Signal(bool, str)  # Success flag, error message if any
    
    def __init__(self, market_service):
        """
        Initialize the data loader thread.
        
        Args:
            market_service: The market service to use for data loading
        """
        super().__init__()
        self.market_service = market_service
        self._is_running = False
        self._should_cancel = False
    
    def run(self):
        """Run the data loading operation in the background thread."""
        self._is_running = True
        self._should_cancel = False
        try:
            while not self._should_cancel:
                logger.info("Starting background market data reload")
                
                # Perform the data loading operation
                success = self.market_service.reload_market_data()
                
                # Check if we should cancel after loading
                if self._should_cancel:
                    logger.info("Background market data reload was cancelled after loading")
                    self.finished.emit(False, "Operation cancelled")
                    break
                    
                if success:
                    logger.info("Background market data reload completed successfully")
                    self.finished.emit(True, "")
                else:
                    logger.error("Background market data reload failed")
                    self.finished.emit(False, "Failed to reload market data")
                
                # Only run once, not in a continuous loop
                break
                
        except Exception as e:
            logger.error(f"Error in background market data reload: {e}", exc_info=True)
            self.finished.emit(False, str(e))
        finally:
            self._is_running = False
            
    def cancel(self):
        """
        Request cancellation of the operation.
        
        Sets the cancellation flag that will be checked during execution to allow
        for graceful termination of the thread instead of using terminate().
        """
        logger.info("Cancellation requested for data loader")
        self._should_cancel = True
            
    def is_active(self):
        """
        Check if the thread is still processing data.
        
        Returns:
            bool: True if the thread is still running, False otherwise
        """
        return self._is_running


class OrderLoader(QThread):
    """
    Background thread for loading market orders without freezing the UI.
    
    Features:
    - Safe cancellation mechanism using a flag instead of direct termination
    - Proper signal handling for communicating loaded data back to the main thread
    - Status tracking to monitor active state
    """
    
    # Define signals for communication with the main thread
    orders_loaded = Signal(list, list)  # buy_orders, sell_orders
    error_occurred = Signal(str)  # error message
    
    def __init__(self, market_service, item_id, trading_hub_id=None, limit=20):
        """
        Initialize the order loader thread.
        
        Args:
            market_service: The market service to use for data loading
            item_id: The ID of the item to load orders for
            trading_hub_id: Optional trading hub ID for reference (not used in query)
            limit: Maximum number of orders to load
        """
        super().__init__()
        self.market_service = market_service
        self.item_id = item_id
        self.trading_hub_id = trading_hub_id
        self.limit = limit
        self._is_running = False
        self._should_cancel = False
    
    def run(self):
        """Run the order loading operation in the background thread."""
        self._is_running = True
        self._should_cancel = False
        try:
            while not self._should_cancel:
                logger.info(f"Starting background order loading for item {self.item_id}")
                
                # Load buy orders - don't filter by region_id since it's not supported
                buy_orders = self.market_service.get_market_data(
                    item_id=self.item_id,
                    order_type="buy",
                    limit=self.limit
                )
                
                # Check for cancellation
                if self._should_cancel:
                    logger.info(f"Background order loading for item {self.item_id} was cancelled after loading buy orders")
                    self.error_occurred.emit("Operation cancelled")
                    break
                
                # Load sell orders - don't filter by region_id since it's not supported
                sell_orders = self.market_service.get_market_data(
                    item_id=self.item_id,
                    order_type="sell",
                    limit=self.limit
                )
                
                logger.info(f"Loaded {len(buy_orders)} buy orders and {len(sell_orders)} sell orders")
                self.orders_loaded.emit(buy_orders, sell_orders)
                
                # Only run once, not in a continuous loop
                break
                
        except Exception as e:
            logger.error(f"Error in background order loading: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False
            
    def cancel(self):
        """
        Request cancellation of the operation.
        
        Sets the cancellation flag that will be checked during execution to allow
        for graceful termination of the thread instead of using terminate().
        """
        logger.info(f"Cancellation requested for order loader (item {self.item_id})")
        self._should_cancel = True
            
    def is_active(self):
        """
        Check if the thread is still processing data.
        
        Returns:
            bool: True if the thread is still running, False otherwise
        """
        return self._is_running


class OrderBookModel(QAbstractTableModel):
    """
    Model for order book data following the Qt Model-View architecture.
    """
    
    def __init__(self, orders=None, station_names=None):
        """
        Initialize the order book model.
        
        Args:
            orders: List of order objects
            station_names: Dictionary mapping station IDs to names
        """
        super().__init__()
        self.orders = orders or []
        self.station_names = station_names or {}
        self.headers = ORDER_COLUMNS
    
    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows in the model."""
        return len(self.orders)
    
    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns in the model."""
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Return data for the given index and role.
        
        Args:
            index: Model index to get data for
            role: Data role (display, edit, etc.)
            
        Returns:
            Data for the given index and role
        """
        if not index.isValid() or not (0 <= index.row() < len(self.orders)):
            return None
        
        order = self.orders[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            # Price column
            if column == 0:
                price = None
                # Handle different order data formats safely
                if isinstance(order, dict):
                    price = order.get('buy_price', order.get('sell_price'))
                else:
                    price = getattr(order, 'buy_price', None) or getattr(order, 'sell_price', None)
                
                return f"{price:,.2f} ISK" if price else "0.00 ISK"
            
            # Quantity column
            elif column == 1:
                volume = None
                # Handle different order data formats safely
                if isinstance(order, dict):
                    volume = order.get('buy_volume', order.get('sell_volume'))
                else:
                    volume = getattr(order, 'buy_volume', None) or getattr(order, 'sell_volume', None)
                
                return f"{volume:,}" if volume else "0"
            
            # Location column
            elif column == 2:
                station_id = None
                # Handle different order data formats safely
                if isinstance(order, dict):
                    station_id = order.get('station_id')
                else:
                    station_id = getattr(order, 'station_id', None)
                
                if station_id is not None:
                    # Convert to string for lookup to ensure consistency
                    return self.station_names.get(station_id, f"Station {station_id}")
                return "Unknown"
            
            # Updated column
            elif column == 3:
                timestamp = None
                # Handle different order data formats safely
                if isinstance(order, dict):
                    timestamp = order.get('timestamp')
                else:
                    timestamp = getattr(order, 'timestamp', None)
                
                if timestamp:
                    return timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(timestamp, 'strftime') else str(timestamp)
                return "Unknown"
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Return header data for the given section, orientation, and role.
        
        Args:
            section: Header section index
            orientation: Header orientation (horizontal or vertical)
            role: Data role (display, edit, etc.)
            
        Returns:
            Header data for the given section, orientation, and role
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        
        return None
        
    def setOrders(self, orders, station_names=None):
        """
        Set the orders for the model.
        
        Args:
            orders: List of order objects
            station_names: Dictionary mapping station IDs to names
        """
        self.beginResetModel()
        self.orders = orders or []
        if station_names:
            self.station_names = station_names
        self.endResetModel()


class MarketDataTab(QWidget):
    """Market Data tab for viewing and analyzing market data."""
    
    def __init__(self, db: Session):
        """
        Initialize the Market Data tab.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__()
        
        # Initialize services
        self.db = db
        self.search_service = SearchService(db)
        self.market_service = MarketService(db)
        
        # State tracking
        self.selected_item_id = None
        self.selected_trading_hub_id = None
        
        # Thread tracking
        self._active_data_loader = None
        self._active_order_loader = None
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals to slots
        self._connect_signals()
        
        # Load trading hubs
        self._load_trading_hubs()
        
        logger.info("Market Data tab initialized")
    
    def closeEvent(self, event):
        """
        Clean up resources when the widget is being closed.
        
        Implements a safe shutdown process:
        1. Calls _clean_up_threads to ensure all background threads are terminated
        2. Processes events to allow thread cleanup operations to complete
        3. Uses a timer to ensure thread cleanup has fully completed before proceeding
        4. Only then allows the original close event to proceed
        
        Args:
            event: Close event
        """
        # Clean up any running threads
        self._clean_up_threads()
        
        # Process events to allow thread cleanup operations to complete
        QApplication.processEvents()
        
        # Ensure threads are really gone before continuing
        QTimer.singleShot(100, lambda: super().closeEvent(event))
        
        # Continue with original close event for now
        super().closeEvent(event)
    
    def _clean_up_threads(self):
        """
        Clean up any running background threads.
        
        Implements a robust thread cleanup strategy:
        1. Requests cancellation of the thread using the cancel() method
        2. Calls quit() to stop the event loop
        3. Waits for the thread to finish with a timeout
        4. Only uses terminate() as a last resort if the thread doesn't exit cleanly
        5. Properly nullifies thread references to avoid memory leaks
        """
        # Clean up data loader thread
        if self._active_data_loader:
            logger.info("Cleaning up data loader thread")
            if self._active_data_loader.isRunning():
                self._active_data_loader.cancel()
                self._active_data_loader.quit()
                if not self._active_data_loader.wait(3000):  # 3 second timeout
                    logger.warning("Data loader thread did not exit cleanly, forcing termination")
                    self._active_data_loader.terminate()
                    self._active_data_loader.wait()
            self._active_data_loader = None

        # Clean up order loader thread
        if self._active_order_loader:
            logger.info("Cleaning up order loader thread")
            if self._active_order_loader.isRunning():
                self._active_order_loader.cancel()
                self._active_order_loader.quit()
                if not self._active_order_loader.wait(3000):  # 3 second timeout
                    logger.warning("Order loader thread did not exit cleanly, forcing termination")
                    self._active_order_loader.terminate()
                    self._active_order_loader.wait()
            self._active_order_loader = None
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget for different analysis views
        self.analysis_tabs = QTabWidget()
        
        # Create Market Analysis tab (existing functionality)
        self.market_analysis_tab = QWidget()
        self._init_market_analysis_ui()
        self.analysis_tabs.addTab(self.market_analysis_tab, "Market Analysis")
        
        # Create Profitability Analysis tab (new functionality)
        self.profitability_tab = QWidget()
        self._init_profitability_analysis_ui()
        self.analysis_tabs.addTab(self.profitability_tab, "Profitability Analysis")
        
        # Add tabs to main layout
        main_layout.addWidget(self.analysis_tabs)
        
        # Set layout
        self.setLayout(main_layout)
    
    def _init_market_analysis_ui(self):
        """Initialize the UI components for market analysis."""
        # Main layout for market analysis tab
        market_layout = QVBoxLayout(self.market_analysis_tab)
        
        # Search panel
        search_group = QGroupBox("Item Search")
        search_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for items...")
        self.search_input.textChanged.connect(self.search_items)
        search_layout.addWidget(self.search_input, 3)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        # Populate categories
        categories = self.search_service.get_categories()
        for category in sorted(categories, key=lambda x: x.name):
            self.category_filter.addItem(category.name, category.id)
        self.category_filter.currentIndexChanged.connect(self.search_items)
        search_layout.addWidget(self.category_filter, 1)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_items)
        search_layout.addWidget(self.search_button)
        
        # Reload market data button
        self.reload_button = QPushButton("Reload Market Data")
        self.reload_button.clicked.connect(self.reload_market_data)
        search_layout.addWidget(self.reload_button)
        
        search_group.setLayout(search_layout)
        market_layout.addWidget(search_group)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side - search results
        self.results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(len(RESULTS_COLUMNS))
        self.results_table.setHorizontalHeaderLabels(RESULTS_COLUMNS)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.itemSelectionChanged.connect(self.update_market_data)
        
        results_layout.addWidget(self.results_table)
        self.results_group.setLayout(results_layout)
        
        # Right side - market data
        self.market_group = QGroupBox("Market Data")
        market_data_layout = QVBoxLayout()
        
        # Create tabs for different market views
        self.market_tabs = QTabWidget()
        
        # Price History tab
        self.price_history_tab = QWidget()
        price_history_layout = QVBoxLayout(self.price_history_tab)
        
        # Chart for price history
        self.price_chart = self._create_price_chart()
        price_history_layout.addWidget(self.price_chart)
        
        # Date range selector
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        date_range_layout.addWidget(self.from_date)
        
        date_range_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        date_range_layout.addWidget(self.to_date)
        
        self.update_chart_button = QPushButton("Update Chart")
        self.update_chart_button.clicked.connect(self.update_price_chart)
        date_range_layout.addWidget(self.update_chart_button)
        
        price_history_layout.addLayout(date_range_layout)
        
        # Trading Hubs tab
        self.trading_hubs_tab = QWidget()
        trading_hubs_layout = QVBoxLayout(self.trading_hubs_tab)
        
        # Trading hub selection
        hub_selection_layout = QHBoxLayout()
        hub_selection_layout.addWidget(QLabel("Select Trading Hubs:"))
        
        # Trading hub checkboxes
        self.hub_checkboxes = {}
        self.trading_hubs = self.market_service.get_trading_hubs()
        
        for hub in self.trading_hubs:
            checkbox = QCheckBox(hub.get('name', str(hub.get('id'))))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_hub_comparison)
            self.hub_checkboxes[hub.get('id')] = checkbox
            hub_selection_layout.addWidget(checkbox)
        
        trading_hubs_layout.addLayout(hub_selection_layout)
        
        # Hub comparison table
        self.hub_comparison_table = QTableWidget()
        self.hub_comparison_table.setColumnCount(len(HUB_COMPARISON_COLUMNS))
        self.hub_comparison_table.setHorizontalHeaderLabels(HUB_COMPARISON_COLUMNS)
        self.hub_comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        trading_hubs_layout.addWidget(self.hub_comparison_table)
        
        # Order Book tab
        self.order_book_tab = QWidget()
        order_book_layout = QVBoxLayout(self.order_book_tab)
        
        # Order book tables
        orders_layout = QHBoxLayout()
        
        # Sell orders
        sell_group = QGroupBox("Sell Orders")
        sell_layout = QVBoxLayout()
        self.sell_orders_table = QTableView()
        self.sell_orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Initialize sell order model
        self.sell_order_model = OrderBookModel()
        self.sell_orders_table.setModel(self.sell_order_model)
        sell_layout.addWidget(self.sell_orders_table)
        sell_group.setLayout(sell_layout)
        orders_layout.addWidget(sell_group)
        
        # Buy orders
        buy_group = QGroupBox("Buy Orders")
        buy_layout = QVBoxLayout()
        self.buy_orders_table = QTableView()
        self.buy_orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Initialize buy order model
        self.buy_order_model = OrderBookModel()
        self.buy_orders_table.setModel(self.buy_order_model)
        buy_layout.addWidget(self.buy_orders_table)
        buy_group.setLayout(buy_layout)
        orders_layout.addWidget(buy_group)
        
        order_book_layout.addLayout(orders_layout)
        
        # Add tabs to market tabs
        self.market_tabs.addTab(self.price_history_tab, "Price History")
        self.market_tabs.addTab(self.trading_hubs_tab, "Trading Hubs")
        self.market_tabs.addTab(self.order_book_tab, "Order Book")
        
        market_data_layout.addWidget(self.market_tabs)
        
        # Item details
        self.item_details_group = QGroupBox("Item Details")
        item_details_layout = QFormLayout()
        
        self.item_name_label = QLabel("Select an item")
        item_details_layout.addRow("Name:", self.item_name_label)
        
        self.item_category_label = QLabel("")
        item_details_layout.addRow("Category:", self.item_category_label)
        
        self.item_volume_label = QLabel("")
        item_details_layout.addRow("Volume:", self.item_volume_label)
        
        self.item_base_price_label = QLabel("")
        item_details_layout.addRow("Base Price:", self.item_base_price_label)
        
        self.item_details_group.setLayout(item_details_layout)
        market_data_layout.addWidget(self.item_details_group)
        
        self.market_group.setLayout(market_data_layout)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.results_group)
        self.main_splitter.addWidget(self.market_group)
        self.main_splitter.setSizes([300, 700])
        
        market_layout.addWidget(self.main_splitter)
        self.market_analysis_tab.setLayout(market_layout)
    
    def _init_profitability_analysis_ui(self):
        """Initialize the UI components for profitability analysis."""
        # Create layout for profitability tab
        profitability_layout = QVBoxLayout(self.profitability_tab)
        
        # Create profitability analyzer widget
        self.profitability_analyzer = ProfitabilityAnalyzerWidget(self.db)
        profitability_layout.addWidget(self.profitability_analyzer)
        
        # Set layout
        self.profitability_tab.setLayout(profitability_layout)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        self.search_button.clicked.connect(self.search_items)
        self.search_input.returnPressed.connect(self.search_items)
        self.results_table.itemSelectionChanged.connect(self.update_market_data)
        self.update_chart_button.clicked.connect(self.update_price_chart)
        self.reload_button.clicked.connect(self.reload_market_data)
        
        # Connect tab change signal
        self.analysis_tabs.currentChanged.connect(self._on_tab_changed)
    
    @Slot(int)
    def _on_tab_changed(self, index):
        """
        Handle tab change event.
        
        Implements resource management when switching between tabs:
        1. Monitors tab changes to detect when the user switches away from the Market Analysis tab
        2. When switching away, cleans up any running threads to conserve resources
        3. Prevents potential thread leaks or race conditions when the tab is not visible
        
        Args:
            index: New tab index
        """
        # Clean up threads when leaving the Market Analysis tab (index 0)
        if index != 0:
            self._clean_up_threads()
    
    def _load_trading_hubs(self):
        """Load trading hubs and create checkboxes."""
        # Clear existing checkboxes
        for checkbox in self.hub_checkboxes.values():
            checkbox.setParent(None)
        self.hub_checkboxes.clear()
        
        # Get trading hubs from the service
        self.trading_hubs = self.market_service.get_trading_hubs()
        logger.info(f"Retrieved {len(self.trading_hubs)} trading hubs from service")
        
        # Create checkboxes dynamically
        for hub in self.trading_hubs:
            # If it's a dictionary (from MarketLogParser)
            if isinstance(hub, dict):
                hub_id = hub.get('id')
                hub_name = hub.get('name', str(hub_id))
                logger.debug(f"Added hub from logs: {hub_name} (ID: {hub_id})")
            # If it's a TradingHub object (from database)
            else:
                hub_id = hub.id
                hub_name = hub.name
                logger.debug(f"Added hub from database: {hub_name} (ID: {hub_id})")
            
            # Create checkbox
            checkbox = QCheckBox(hub_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_hub_comparison)
            self.hub_checkboxes[hub_id] = checkbox
        
        logger.info(f"Created {len(self.hub_checkboxes)} trading hub checkboxes")
    
    def _show_loading_state(self, widget, is_loading: bool):
        """
        Show or hide loading indicators for a widget.
        
        Creates a semi-transparent overlay with "Loading..." text for better
        visual feedback during long operations. Implementation features:
        
        1. Safe resize event handling without relying on sip.isdeleted
        2. Proper storage and restoration of the original resize event handler
        3. Ensures overlay is always properly sized regardless of widget resizing
        4. Cleans up resources when the overlay is no longer needed
        
        Args:
            widget: The widget to show loading state for
            is_loading: Whether the widget is in a loading state
        """
        if not widget:
            return
            
        # Find existing overlay
        overlay = widget.findChild(QLabel, "loadingOverlay")
        
        if is_loading:
            # Set wait cursor for entire application
            QApplication.setOverrideCursor(Qt.WaitCursor)
            widget.setEnabled(False)
            
            # Create overlay if it doesn't exist
            if not overlay:
                overlay = QLabel(widget)
                overlay.setObjectName("loadingOverlay")
                overlay.setText("Loading...")
                overlay.setAlignment(Qt.AlignCenter)
                
                # Make semi-transparent
                overlay.setStyleSheet("""
                    background-color: rgba(0, 0, 0, 50%);
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                """)
                
                # Size the overlay to cover the widget
                overlay.setFixedSize(widget.size())
                
                # Center in parent widget
                overlay.move(0, 0)
                
                # Store original resize event handler
                if not hasattr(widget, '_oldResizeEvent'):
                    widget._oldResizeEvent = widget.resizeEvent
                
                # Create a safe resize handler that checks if overlay exists
                def safeResizeHandler(event):
                    # Check if overlay still exists by searching the widget's children
                    overlay_obj = widget.findChild(QLabel, "loadingOverlay")
                    if overlay_obj:
                        overlay_obj.resize(event.size())
                    # Call the original resize handler
                    if hasattr(widget, '_oldResizeEvent') and widget._oldResizeEvent:
                        widget._oldResizeEvent(event)
                
                # Set the new resize handler
                widget.resizeEvent = safeResizeHandler
                
                # Bring to front
                overlay.raise_()
                overlay.show()
        else:
            # Restore normal cursor
            QApplication.restoreOverrideCursor()
            widget.setEnabled(True)
            
            # Remove the overlay if it exists
            if overlay:
                # Restore original resize event
                if hasattr(widget, '_oldResizeEvent'):
                    widget.resizeEvent = widget._oldResizeEvent
                    delattr(widget, '_oldResizeEvent')
                
                # Delete overlay safely
                overlay.hide()
                overlay.deleteLater()
    
    @Slot()
    def search_items(self):
        """Search for items based on the search input and category filter."""
        # Show loading state
        self._show_loading_state(self.search_button, True)
        
        try:
            # Get and sanitize search term
            search_term = self.search_input.text().strip()
            
            # Limit length to prevent performance issues or injection
            if len(search_term) > 100:
                search_term = search_term[:100]
                logger.warning(f"Search term truncated to 100 characters: {search_term}")
            
            # Get selected category ID
            category_id = None
            if self.category_filter.currentIndex() > 0:
                category_id = self.category_filter.currentData()
            
            # Log search attempt
            logger.info(f"Searching for items with term: '{search_term}', category_id: {category_id}")
            
            # Search for items
            items = self.search_service.search_items(search_term, category_id=category_id)
            
            # Update results table
            self.results_table.setRowCount(len(items))
            
            for i, item in enumerate(items):
                self.results_table.setItem(i, 0, QTableWidgetItem(item.name))
                category_name = item.group.category.name if item.group and item.group.category else ""
                self.results_table.setItem(i, 1, QTableWidgetItem(category_name))
                
                # Store item ID in the first column
                self.results_table.item(i, 0).setData(Qt.UserRole, item.id)
                
            logger.info(f"Found {len(items)} items matching search term '{search_term}'")
        except Exception as e:
            logger.error(f"Error searching for items: {e}", exc_info=True)
            QMessageBox.warning(self, "Search Error", f"An error occurred while searching: {str(e)}")
        finally:
            # Restore cursor
            self._show_loading_state(self.search_button, False)
    
    def _update_results_table(self, items: List[Item]):
        """
        Update the results table with the given items.
        
        Args:
            items: List of Item objects to display
        """
        # Clear the table
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        
        # Add items to the table
        for row, item in enumerate(items):
            self.results_table.insertRow(row)
            
            # Item name
            name_item = QTableWidgetItem(item.name)
            name_item.setData(Qt.UserRole, item.id)  # Store item ID
            self.results_table.setItem(row, 0, name_item)
            
            # Category name
            category_name = item.group.category.name if item.group and item.group.category else "N/A"
            category_item = QTableWidgetItem(category_name)
            self.results_table.setItem(row, 1, category_item)
        
        logger.debug(f"Updated results table with {len(items)} items")
        
        # Clear market data 
        self._clear_market_data()
    
    def _clear_market_data(self):
        """Clear all market data displays."""
        # Clear price history chart
        self.price_chart.setChart(QChart())
        
        # Clear order book tables
        self.buy_orders_table.clearContents()
        self.buy_orders_table.setRowCount(0)
        self.sell_orders_table.clearContents()
        self.sell_orders_table.setRowCount(0)
        
        # Clear hub comparison table
        self.hub_comparison_table.clearContents()
        self.hub_comparison_table.setRowCount(0)
        
        # Clear item details
        self.item_name_label.setText("Select an item")
        self.item_category_label.setText("")
        self.item_volume_label.setText("")
        self.item_base_price_label.setText("")
    
    @Slot()
    def update_market_data(self):
        """Update all market data displays for the current item and trading hub."""
        # Get the selected item from the table
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            logger.warning("No item selected in results table")
            return
        
        # Get the item ID from the name column (column 0)
        row = selected_items[0].row()
        item_cell = self.results_table.item(row, 0)
        item_name = item_cell.text()
        item_id = item_cell.data(Qt.UserRole)
        self.selected_item_id = item_id
        
        logger.info(f"Selected item: '{item_name}' (ID: {item_id})")
        
        # Get the first selected trading hub
        trading_hub_id = None
        trading_hub_name = "Unknown"
        
        for hub_id, checkbox in self.hub_checkboxes.items():
            if checkbox.isChecked():
                trading_hub_id = hub_id
                trading_hub_name = checkbox.text()
                break
        
        if not trading_hub_id and self.trading_hubs:
            # Use the first trading hub as default if none selected
            hub = self.trading_hubs[0]
            trading_hub_id = hub.get('id') if isinstance(hub, dict) else hub.id
            trading_hub_name = hub.get('name', str(trading_hub_id)) if isinstance(hub, dict) else hub.name
            logger.warning(f"No trading hub selected, using default: {trading_hub_name}")
        
        self.selected_trading_hub_id = trading_hub_id
        
        logger.info(f"Updating market data for item ID {self.selected_item_id} at hub '{trading_hub_name}' (ID: {trading_hub_id})")
        
        # Update the price history chart
        self.update_price_chart()
        
        # Update the order book
        self.update_order_book()
        
        # Update the trading hub comparison
        self.update_hub_comparison()
        
        # Update item details
        item = self.db.query(Item).filter(Item.id == self.selected_item_id).first()
        if item:
            self.item_name_label.setText(item.name)
            self.item_category_label.setText(item.group.category.name if item.group and item.group.category else "")
            self.item_volume_label.setText(f"{item.volume:.2f} m³" if item.volume else "")
    
    def _create_price_chart(self):
        """Create a chart for displaying price history."""
        # Create chart
        chart = QChart()
        chart.setTitle("Price History")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
    
    def update_price_chart(self):
        """Update the price history chart for the selected item."""
        if not self.selected_item_id:
            return
        
        # Show loading state
        self._show_loading_state(self.price_chart, True)
        
        try:
            # Get date range
            from_date = self.from_date.date().toPython()
            to_date = self.to_date.date().toPython()
            
            # Validate date range
            if from_date > to_date:
                QMessageBox.warning(self, "Invalid Date Range", "Start date must be before end date")
                return
            
            # Get price history
            history = self.market_service.get_market_statistics(
                self.selected_item_id,
                days=(to_date - from_date).days + 1
            )
            
            # Clean up old chart to prevent memory leaks
            old_chart = self.price_chart.chart()
            if old_chart:
                old_chart.deleteLater()
            
            # Create chart
            chart = QChart()
            chart.setTitle("Price History")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series for sell and buy prices
            sell_series = QLineSeries()
            sell_series.setName("Sell Price")
            
            buy_series = QLineSeries()
            buy_series.setName("Buy Price")
            
            # Add data points
            if history and 'price_history' in history:
                for point in history['price_history']:
                    date = datetime.datetime.fromisoformat(point['date']).timestamp() * 1000
                    sell_series.append(date, point['sell'])
                    buy_series.append(date, point['buy'])
            else:
                # Add single data point with current price if no history
                now = datetime.datetime.now().timestamp() * 1000
                current_stats = self.market_service.get_market_statistics(self.selected_item_id, days=1)
                
                if current_stats:
                    sell_series.append(now, current_stats.get('sell_price', 0))
                    buy_series.append(now, current_stats.get('buy_price', 0))
                    
                    # Add note about limited data
                    chart.setTitle("Price History (Limited Data Available)")
            
            # Add series to chart
            chart.addSeries(sell_series)
            chart.addSeries(buy_series)
            
            # Create axes
            date_axis = QDateTimeAxis()
            date_axis.setTitleText("Date")
            date_axis.setFormat("MMM dd")
            chart.addAxis(date_axis, Qt.AlignBottom)
            sell_series.attachAxis(date_axis)
            buy_series.attachAxis(date_axis)
            
            value_axis = QValueAxis()
            value_axis.setTitleText("Price (ISK)")
            chart.addAxis(value_axis, Qt.AlignLeft)
            sell_series.attachAxis(value_axis)
            buy_series.attachAxis(value_axis)
            
            # Set the chart
            self.price_chart.setChart(chart)
        except Exception as e:
            logger.error(f"Error updating price chart: {e}", exc_info=True)
            QMessageBox.warning(self, "Chart Error", f"An error occurred while updating the price chart: {str(e)}")
        finally:
            # Restore cursor
            self._show_loading_state(self.price_chart, False)
    
    def update_order_book(self):
        """
        Update the order book tables.
        
        Implements thread-safe order loading:
        1. Validates that required data is available
        2. Shows loading state to provide visual feedback
        3. Cleans up any existing order loader thread
        4. Resets models to handle UI state properly
        5. Creates a new thread with proper parent-child relationship
        6. Connects signals for handling loaded orders and errors
        7. Tracks the active thread for proper cleanup
        """
        if not self.selected_item_id or not self.selected_trading_hub_id:
            logger.warning("Cannot update order book: No item or hub selected")
            return
        
        logger.info(f"Updating order book for item ID {self.selected_item_id}")
        
        # Show loading state
        self._show_loading_state(self.order_book_tab, True)
        
        # Clean up any existing order loader
        if self._active_order_loader:
            if self._active_order_loader.isRunning():
                self._active_order_loader.cancel()
                self._active_order_loader.wait()
            self._active_order_loader = None
        
        # Clear existing tables
        # Reset models to empty
        self.buy_order_model.setOrders([])
        self.sell_order_model.setOrders([])
        
        # Create the order loader thread
        self.order_loader = OrderLoader(
            self.market_service, 
            self.selected_item_id,
            self.selected_trading_hub_id,
            limit=20
        )
        self.order_loader.setParent(self)  # Ensure proper parent-child relationship
        
        # Connect signals
        self.order_loader.orders_loaded.connect(self._populate_order_tables)
        self.order_loader.error_occurred.connect(self._handle_order_load_error)
        
        # Start the background thread - Keep a reference to the thread
        self._active_order_loader = self.order_loader
        self.order_loader.start()
    
    def _populate_order_tables(self, buy_orders, sell_orders):
        """
        Populate order book tables with the loaded orders.
        
        Args:
            buy_orders: List of buy orders
            sell_orders: List of sell orders
        """
        try:
            # Validate the input
            if buy_orders is None:
                buy_orders = []
            if sell_orders is None:
                sell_orders = []
            
            # Ensure they are lists
            if not isinstance(buy_orders, list):
                logger.error(f"Expected buy_orders to be a list, got {type(buy_orders)}")
                buy_orders = []
            if not isinstance(sell_orders, list):
                logger.error(f"Expected sell_orders to be a list, got {type(sell_orders)}")
                sell_orders = []
            
            # Get a mapping of station IDs to names
            station_ids = []
            for o in buy_orders + sell_orders:
                # Handle both object and dictionary formats
                if isinstance(o, dict):
                    if 'station_id' in o and o['station_id']:
                        station_ids.append(o['station_id'])
                else:
                    if hasattr(o, 'station_id') and o.station_id:
                        station_ids.append(o.station_id)
                    
            station_ids = list(set(station_ids))  # Deduplicate
            logger.debug(f"Looking up names for {len(station_ids)} station IDs")
            
            station_names = self._get_station_names(station_ids)
            
            # Update buy orders model
            self.buy_order_model.setOrders(buy_orders, station_names)
            
            # Update sell orders model
            self.sell_order_model.setOrders(sell_orders, station_names)
            
            logger.info(f"Order book updated with {len(buy_orders)} buy orders and {len(sell_orders)} sell orders")
        except Exception as e:
            logger.error(f"Error populating order tables: {e}", exc_info=True)
            QMessageBox.warning(self, "Order Book Error", f"An error occurred while loading orders: {str(e)}")
        finally:
            # Restore cursor
            self._show_loading_state(self.order_book_tab, False)
            
            # Clean up the thread safely
            if self._active_order_loader:
                # Disconnect signals
                try:
                    self._active_order_loader.orders_loaded.disconnect()
                    self._active_order_loader.error_occurred.disconnect()
                except (RuntimeError, TypeError) as e:
                    # Signal was already disconnected
                    logger.warning(f"Signal disconnect error: {e}")
                
                # Thread should already be finished, but wait just in case
                if self._active_order_loader.isRunning():
                    self._active_order_loader.wait()
                
                # Now safe to clean up
                self._active_order_loader = None
    
    def _handle_order_load_error(self, error_message: str):
        """
        Handle errors that occur during order loading.
        
        Args:
            error_message: Error message from the thread
        """
        logger.error(f"Error loading orders: {error_message}")
        QMessageBox.warning(self, "Order Book Error", f"An error occurred while loading orders: {error_message}")
        
        # Restore cursor
        self._show_loading_state(self.order_book_tab, False)
        
        # Clean up the thread safely
        if self._active_order_loader:
            # Disconnect signals
            try:
                self._active_order_loader.orders_loaded.disconnect()
                self._active_order_loader.error_occurred.disconnect()
            except (RuntimeError, TypeError) as e:
                # Signal was already disconnected
                logger.warning(f"Signal disconnect error: {e}")
            
            # Thread should already be finished, but wait just in case
            if self._active_order_loader.isRunning():
                self._active_order_loader.wait()
            
            # Now safe to clean up
            self._active_order_loader = None
    
    def _get_station_names(self, station_ids: List[int]) -> Dict[int, str]:
        """
        Get a mapping of station IDs to names.
        
        Uses the MarketService to batch lookup station names.
        
        Args:
            station_ids: List of station IDs to look up
            
        Returns:
            Dictionary mapping station IDs to names
        """
        if not station_ids:
            return {}
        
        try:
            # Use the market service's batch method to get station names
            station_names = self.market_service.batch_get_station_names(station_ids)
            
            # Validate the response
            if station_names is None or not isinstance(station_names, dict):
                logger.error(f"Invalid station names response: {station_names}")
                return {sid: f"Station {sid}" for sid in station_ids}
            
            # Ensure all requested station IDs have a name
            for sid in station_ids:
                if sid not in station_names:
                    station_names[sid] = f"Station {sid}"
                
            return station_names
        except Exception as e:
            logger.error(f"Error looking up station names: {e}", exc_info=True)
            # Fallback to providing generic station names
            return {sid: f"Station {sid}" for sid in station_ids}
    
    @Slot()
    def reload_market_data(self):
        """
        Reload market data from log files and refresh the UI.
        
        Implements thread-safe data loading:
        1. Shows loading state to provide visual feedback
        2. Cleans up any existing data loader thread
        3. Creates a new thread with proper parent-child relationship
        4. Connects signals for handling success and failure
        5. Tracks the active thread for proper cleanup
        """
        logger.info("Starting market data reload")
        
        # Show loading state
        self._show_loading_state(self.reload_button, True)
        self.reload_button.setText("Loading...")
        
        # Clean up any existing data loader
        if self._active_data_loader:
            if self._active_data_loader.isRunning():
                self._active_data_loader.cancel()
                self._active_data_loader.wait()
            self._active_data_loader = None
        
        # Create the data loader thread
        self.data_loader = DataLoader(self.market_service)
        self.data_loader.setParent(self)  # Ensure proper parent-child relationship
        
        # Connect signals - use specific method signatures for better control
        self.data_loader.finished.connect(self._on_data_reload_finished)
        
        # Start the background thread - Keep a reference to the thread
        self._active_data_loader = self.data_loader
        self.data_loader.start()
    
    @Slot(bool, str)
    def _on_data_reload_finished(self, success: bool, error_message: str):
        """
        Handle the completion of data reload.
        
        Args:
            success: Whether the reload was successful
            error_message: Error message if the reload failed
        """
        # Reset button state
        self.reload_button.setText("Reload Market Data")
        self._show_loading_state(self.reload_button, False)
        
        if success:
            # Reload trading hubs
            self._load_trading_hubs()
            
            # Update market data if an item is selected
            if self.selected_item_id:
                self.update_market_data()
                
            # Show success message
            logger.info("Market data successfully reloaded")
            QMessageBox.information(self, "Data Reloaded", "Market data has been successfully reloaded")
        else:
            # Show error message
            logger.error(f"Failed to reload market data: {error_message}")
            QMessageBox.critical(self, "Reload Error", f"Failed to reload market data: {error_message}")
        
        # Clean up the thread safely
        if self._active_data_loader:
            # Disconnect signals
            try:
                self._active_data_loader.finished.disconnect()
            except (RuntimeError, TypeError) as e:
                # Signal was already disconnected
                logger.warning(f"Signal disconnect error: {e}")
            
            # Thread should already be finished, but wait just in case
            if self._active_data_loader.isRunning():
                self._active_data_loader.wait()
            
            # Now safe to clean up
            self._active_data_loader = None

    def update_hub_comparison(self):
        """Update the trading hub comparison table."""
        if not self.selected_item_id:
            return
        
        # Get selected hubs
        selected_hubs = [hub_id for hub_id, checkbox in self.hub_checkboxes.items() if checkbox.isChecked()]
        
        # Get market data
        market_data = self.market_service.get_unified_market_data()
        if not market_data or 'items' not in market_data:
            return
        
        # Get item data - ensure consistent key type (string)
        item_id_str = str(self.selected_item_id)
        item_data = market_data['items'].get(item_id_str, {})
        
        # Clear table
        self.hub_comparison_table.setRowCount(0)
        
        # Add rows for each hub
        row = 0
        for hub_id in selected_hubs:
            # Convert hub_id to string for lookup
            hub_id_str = str(hub_id)
            hub_data = item_data.get(hub_id_str, {})
            if not hub_data:
                continue
            
            self.hub_comparison_table.insertRow(row)
            
            # Hub name
            hub_name = "Unknown"
            for hub in self.trading_hubs:
                # Handle both dict and object formats
                if isinstance(hub, dict):
                    if str(hub.get('id')) == hub_id_str:
                        hub_name = hub.get('name', str(hub_id))
                        break
                else:
                    if str(hub.id) == hub_id_str:
                        hub_name = hub.name
                        break
            
            self.hub_comparison_table.setItem(row, 0, QTableWidgetItem(hub_name))
            
            # Sell price
            sell_price = hub_data.get('sell', 0)
            self.hub_comparison_table.setItem(row, 1, QTableWidgetItem(f"{sell_price:,.2f}"))
            
            # Buy price
            buy_price = hub_data.get('buy', 0)
            self.hub_comparison_table.setItem(row, 2, QTableWidgetItem(f"{buy_price:,.2f}"))
            
            # Spread
            spread = sell_price - buy_price
            spread_pct = (spread / sell_price * 100) if sell_price else 0
            self.hub_comparison_table.setItem(row, 3, QTableWidgetItem(f"{spread:,.2f} ({spread_pct:.2f}%)"))
            
            row += 1 