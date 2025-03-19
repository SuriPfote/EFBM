"""
Profitability Analyzer Widget for EVE Frontier Blueprint Miracle.

This widget allows users to analyze the profitability of manufacturing items.
"""

import logging
from typing import Dict, List, Optional, Any
import time
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTableWidget, QTableWidgetItem,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, 
    QFormLayout, QHeaderView, QFileDialog, QMessageBox,
    QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont

from eve_frontier.services.market_service import MarketService
from eve_frontier.services.production_service import ProductionService
from eve_frontier.services.search_service import SearchService
from eve_frontier.models.item import Item

logger = logging.getLogger(__name__)


class ProfitabilityAnalyzerWidget(QWidget):
    """Widget for analyzing item manufacturing profitability."""
    
    # Signals for worker thread
    analysis_finished = Signal(list)
    analysis_error = Signal(str)
    analysis_progress = Signal(int, int)
    
    def __init__(self, db, parent=None):
        """
        Initialize the profitability analyzer widget.
        
        Args:
            db: SQLAlchemy database session
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize services
        self.db = db
        self.market_service = MarketService(db)
        self.production_service = ProductionService(db)
        self.search_service = SearchService(db)
        
        # State tracking
        self.analysis_results = []
        self.analysis_thread = None
        self.is_analyzing = False
        
        # Initialize UI
        self._init_ui()
        
        logger.info("Profitability analyzer widget initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Settings group
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QFormLayout()
        
        # ME level setting
        self.me_level_spin = QSpinBox()
        self.me_level_spin.setRange(0, 10)
        self.me_level_spin.setValue(0)
        self.me_level_spin.setToolTip("Material Efficiency level to use for calculations")
        settings_layout.addRow("Material Efficiency:", self.me_level_spin)
        
        # Min profit margin setting
        self.min_margin_spin = QDoubleSpinBox()
        self.min_margin_spin.setRange(0, 1000)
        self.min_margin_spin.setValue(5.0)
        self.min_margin_spin.setSuffix("%")
        self.min_margin_spin.setToolTip("Minimum profit margin to include in results")
        settings_layout.addRow("Min Profit Margin:", self.min_margin_spin)
        
        # Include components checkbox
        self.include_components_check = QCheckBox("Include component costs")
        self.include_components_check.setChecked(True)
        self.include_components_check.setToolTip("Whether to include component manufacturing costs or just raw materials")
        settings_layout.addRow("", self.include_components_check)
        
        # Only manufacturable checkbox
        self.only_manufacturable_check = QCheckBox("Only manufacturable items")
        self.only_manufacturable_check.setChecked(True)
        self.only_manufacturable_check.setToolTip("Only include items that can be manufactured from blueprints")
        settings_layout.addRow("", self.only_manufacturable_check)
        
        # Max results
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 1000)
        self.max_results_spin.setValue(100)
        self.max_results_spin.setSingleStep(10)
        self.max_results_spin.setToolTip("Maximum number of results to show")
        settings_layout.addRow("Max Results:", self.max_results_spin)
        
        # Sort by dropdown
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItems(["Profit Margin", "Profit Amount", "Production Cost", "Market Price"])
        self.sort_by_combo.setToolTip("How to sort the results")
        settings_layout.addRow("Sort By:", self.sort_by_combo)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("Analyze Profitability")
        self.analyze_button.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.analyze_button)
        
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        main_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Item", "Production Cost", "Market Price", "Profit", 
            "Profit Margin", "Volume", "ME Level"
        ])
        
        # Set column widths
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            self.results_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSortingEnabled(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemDoubleClicked.connect(self.show_detailed_analysis)
        
        main_layout.addWidget(self.results_table, 1)
        
        # Connect signals
        self.analysis_finished.connect(self.on_analysis_finished)
        self.analysis_error.connect(self.on_analysis_error)
        self.analysis_progress.connect(self.update_progress)
        
        # Set up layout
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
    
    def start_analysis(self):
        """Start the profitability analysis in a background thread."""
        if self.is_analyzing:
            QMessageBox.warning(self, "Analysis in Progress", "Analysis is already running")
            return
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.analysis_results = []
        self.export_button.setEnabled(False)
        
        # Get settings
        me_level = self.me_level_spin.value()
        min_margin = self.min_margin_spin.value()
        include_components = self.include_components_check.isChecked()
        only_manufacturable = self.only_manufacturable_check.isChecked()
        max_results = self.max_results_spin.value()
        
        # Update UI
        self.is_analyzing = True
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading market data...")
        
        # Start analysis in a thread
        self.analysis_thread = threading.Thread(
            target=self._run_analysis,
            args=(me_level, min_margin, include_components, only_manufacturable, max_results)
        )
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
    
    def _run_analysis(self, me_level, min_margin, include_components, only_manufacturable, max_results):
        """
        Run the analysis in a background thread.
        
        Args:
            me_level: Material Efficiency level
            min_margin: Minimum profit margin
            include_components: Whether to include component costs
            only_manufacturable: Only include manufacturable items
            max_results: Maximum number of results to return
        """
        try:
            # Get all items with market data
            logger.info(f"Starting profitability analysis with ME={me_level}, min_margin={min_margin}%, include_components={include_components}, only_manufacturable={only_manufacturable}")
            
            market_data = self.market_service._load_unified_market_data()
            if not market_data or 'items' not in market_data:
                logger.error("No market data available for analysis")
                self.analysis_error.emit("No market data available")
                return
            
            # Get list of all item IDs with market data
            item_ids_with_market_data = list(market_data['items'].keys())
            total_items = len(item_ids_with_market_data)
            logger.info(f"Found {total_items} items with market data")
            
            # Initialize results list
            results = []
            items_processed = 0
            items_missing = 0
            items_not_manufacturable = 0
            items_no_profit_data = 0
            items_below_margin = 0
            
            # Process each item
            for i, item_id in enumerate(item_ids_with_market_data):
                if i % 10 == 0:
                    self.analysis_progress.emit(i, total_items)
                
                try:
                    # Get item details
                    item_id_int = int(item_id)
                    item = self.db.query(Item).filter(
                        Item.id == item_id_int
                    ).first()
                    
                    if not item:
                        items_missing += 1
                        if items_missing <= 5:
                            logger.warning(f"Item not found in database: ID {item_id_int}")
                        continue
                    
                    items_processed += 1
                    
                    # If only_manufacturable, check if the item has a blueprint
                    if only_manufacturable:
                        blueprint = self.production_service._find_manufacturing_blueprint(item_id_int)
                        if not blueprint:
                            items_not_manufacturable += 1
                            if items_not_manufacturable <= 5:
                                logger.debug(f"Item {item.name} (ID: {item_id_int}) has no manufacturing blueprint")
                            continue
                    
                    # Calculate production profit
                    logger.debug(f"Calculating profit for {item.name} (ID: {item_id_int})")
                    profit_data = self.production_service.calculate_production_profit(
                        item_id_int,
                        quantity=1,
                        me_level=me_level,
                        include_components=include_components
                    )
                    
                    # Only include items with profit data
                    if not profit_data or 'profit_margin' not in profit_data:
                        items_no_profit_data += 1
                        if items_no_profit_data <= 5:
                            logger.warning(f"No profit data for {item.name} (ID: {item_id_int})")
                        continue
                    
                    # Filter by minimum profit margin
                    if profit_data['profit_margin'] < min_margin:
                        items_below_margin += 1
                        if items_below_margin <= 5:
                            logger.debug(f"Item {item.name} (ID: {item_id_int}) profit margin {profit_data['profit_margin']:.2f}% is below threshold {min_margin}%")
                        continue
                    
                    # Add to results
                    logger.info(f"Found profitable item: {item.name} - Margin: {profit_data['profit_margin']:.2f}%, Profit: {profit_data.get('profit', 0)}")
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
                    logger.error(f"Error processing item {item_id}: {e}", exc_info=True)
                    continue
            
            logger.info(f"Analysis summary: {items_processed} items processed, {len(results)} profitable items found")
            logger.info(f"Items filtered out: {items_missing} missing, {items_not_manufacturable} not manufacturable, "
                       f"{items_no_profit_data} no profit data, {items_below_margin} below margin threshold")
            
            # Sort results based on selected sort field
            sort_field = {
                0: 'profit_margin',
                1: 'profit',
                2: 'production_cost',
                3: 'market_price'
            }.get(self.sort_by_combo.currentIndex(), 'profit_margin')
            
            results.sort(key=lambda x: x[sort_field], reverse=True)
            
            # Limit results
            if max_results:
                results = results[:max_results]
            
            # Update UI with results
            self.analysis_finished.emit(results)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            self.analysis_error.emit(f"Error during analysis: {str(e)}")
        finally:
            self.analysis_progress.emit(total_items, total_items)
    
    @Slot(list)
    def on_analysis_finished(self, results):
        """
        Handle the completion of the analysis.
        
        Args:
            results: Analysis results
        """
        self.analysis_results = results
        
        # Update table
        self.results_table.setRowCount(len(results))
        
        # Populate table
        for row, item in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(item['item_name']))
            
            # Production cost
            cost_item = QTableWidgetItem()
            cost_item.setData(Qt.DisplayRole, f"{item['production_cost']:,.2f}")
            cost_item.setData(Qt.UserRole, item['production_cost'])
            self.results_table.setItem(row, 1, cost_item)
            
            # Market price
            price_item = QTableWidgetItem()
            price_item.setData(Qt.DisplayRole, f"{item['market_price']:,.2f}")
            price_item.setData(Qt.UserRole, item['market_price'])
            self.results_table.setItem(row, 2, price_item)
            
            # Profit
            profit_item = QTableWidgetItem()
            profit_item.setData(Qt.DisplayRole, f"{item['profit']:,.2f}")
            profit_item.setData(Qt.UserRole, item['profit'])
            self.results_table.setItem(row, 3, profit_item)
            
            # Profit margin
            margin_item = QTableWidgetItem()
            margin_item.setData(Qt.DisplayRole, f"{item['profit_margin']:.2f}%")
            margin_item.setData(Qt.UserRole, item['profit_margin'])
            self.results_table.setItem(row, 4, margin_item)
            
            # Volume
            volume_item = QTableWidgetItem()
            volume_item.setData(Qt.DisplayRole, f"{item['volume']:,}")
            volume_item.setData(Qt.UserRole, item['volume'])
            self.results_table.setItem(row, 5, volume_item)
            
            # ME level
            me_item = QTableWidgetItem()
            me_item.setData(Qt.DisplayRole, str(item['material_efficiency']))
            me_item.setData(Qt.UserRole, item['material_efficiency'])
            self.results_table.setItem(row, 6, me_item)
            
            # Store item ID in the first column for later reference
            self.results_table.item(row, 0).setData(Qt.UserRole, item['item_id'])
        
        # Update UI state
        self.is_analyzing = False
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        
        if results:
            self.status_label.setText(f"Analysis complete. Found {len(results)} profitable items.")
        else:
            self.status_label.setText("Analysis complete. No profitable items found.")
    
    @Slot(str)
    def on_analysis_error(self, error_message):
        """
        Handle analysis errors.
        
        Args:
            error_message: Error message
        """
        self.is_analyzing = False
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText(f"Error: {error_message}")
        QMessageBox.critical(self, "Analysis Error", error_message)
    
    @Slot(int, int)
    def update_progress(self, current, total):
        """
        Update the progress bar.
        
        Args:
            current: Current progress
            total: Total items to process
        """
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Analyzing items... {current}/{total}")
    
    def export_results(self):
        """Export the analysis results to a CSV file."""
        if not self.analysis_results:
            QMessageBox.warning(self, "No Results", "No results to export")
            return
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "item_profitability.csv", "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # Ensure output directory exists
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Define CSV fields
            import csv
            fields = [
                'item_id', 'item_name', 'production_cost', 'market_price', 
                'profit', 'profit_margin', 'volume', 'material_efficiency'
            ]
            
            # Write CSV file
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for item in self.analysis_results:
                    # Only write fields that are in our field list
                    row = {field: item.get(field, '') for field in fields}
                    writer.writerow(row)
            
            self.status_label.setText(f"Results exported to {output_path}")
            QMessageBox.information(self, "Export Complete", f"Results exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            QMessageBox.critical(self, "Export Error", f"Error exporting results: {str(e)}")
    
    def show_detailed_analysis(self, item):
        """
        Show detailed analysis for the selected item.
        
        Args:
            item: Selected table item
        """
        # Get the item ID from the first column
        row = item.row()
        item_id = self.results_table.item(row, 0).data(Qt.UserRole)
        item_name = self.results_table.item(row, 0).text()
        
        # Get the current ME level
        me_level = self.me_level_spin.value()
        
        # Do the detailed analysis
        try:
            # Get manufacturing details
            manufacturing_details = self.production_service.get_manufacturing_details(
                item_id,
                quantity=1,
                me_level=me_level,
                max_depth=10
            )
            
            if not manufacturing_details:
                QMessageBox.warning(self, "No Details", f"No manufacturing details found for {item_name}")
                return
            
            # Show the details in a dialog
            from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Manufacturing Details: {item_name}")
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            
            # Format the details
            import json
            details_text.setText(json.dumps(manufacturing_details.to_dict(), indent=2))
            
            layout.addWidget(details_text)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error showing details: {e}")
            QMessageBox.critical(self, "Error", f"Error retrieving manufacturing details: {str(e)}") 