"""
Blueprint Browser Tab for EVE Frontier Blueprint Miracle.

This module defines the Blueprint Browser tab which allows users to search for and view 
blueprint information, including materials, products, and manufacturing details.
"""

import logging
from typing import List, Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, QTabWidget,
    QPushButton, QGroupBox, QFormLayout, QSplitter, QHeaderView,
    QCheckBox, QScrollArea, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon

from sqlalchemy.orm import Session

from eve_frontier.models import Blueprint, BlueprintProduct, BlueprintMaterial, BlueprintActivity, Item
from eve_frontier.services.search_service import SearchService
from eve_frontier.services.production_service import ProductionService

logger = logging.getLogger(__name__)

class BlueprintBrowserTab(QWidget):
    """Blueprint Browser tab for searching and viewing blueprints."""
    
    def __init__(self, db: Session):
        """
        Initialize the Blueprint Browser tab.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__()
        
        # Initialize services
        self.db = db
        self.search_service = SearchService(db)
        self.production_service = ProductionService(db)
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals to slots
        self._connect_signals()
        
        logger.info("Blueprint Browser tab initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create search section
        search_group = QGroupBox("Search Blueprints")
        search_layout = QVBoxLayout(search_group)
        
        # Search input row
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter blueprint name or item name...")
        self.search_button = QPushButton("Search")
        self.search_button.setFixedWidth(100)
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_button)
        search_layout.addLayout(search_input_layout)
        
        # Filter options row
        filter_layout = QHBoxLayout()
        
        # Activity filter
        activity_layout = QHBoxLayout()
        activity_layout.addWidget(QLabel("Activity:"))
        self.activity_combo = QComboBox()
        self.activity_combo.addItem("All Activities", None)
        self.activity_combo.addItem("Manufacturing", "manufacturing")
        self.activity_combo.addItem("Copying", "copying")
        self.activity_combo.addItem("Invention", "invention")
        self.activity_combo.addItem("Research ME", "research_material")
        self.activity_combo.addItem("Research TE", "research_time")
        activity_layout.addWidget(self.activity_combo)
        filter_layout.addLayout(activity_layout)
        
        # Published only checkbox
        self.published_only = QCheckBox("Published Only")
        self.published_only.setChecked(True)
        filter_layout.addWidget(self.published_only)
        
        # Add stretch to push everything to the left
        filter_layout.addStretch()
        
        # Results limit
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Limit:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 1000)
        self.limit_spin.setValue(50)
        self.limit_spin.setSingleStep(10)
        limit_layout.addWidget(self.limit_spin)
        filter_layout.addLayout(limit_layout)
        
        search_layout.addLayout(filter_layout)
        
        # Add search section to main layout
        main_layout.addWidget(search_group)
        
        # Create a splitter for results and details
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Blueprint results section
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 10, 0, 0)
        
        results_label = QLabel("Blueprint Results")
        results_label.setFont(QFont(results_label.font().family(), 10, QFont.Bold))
        results_layout.addWidget(results_label)
        
        self.results_table = QTableWidget(0, 3)  # columns: ID, Name, Products
        self.results_table.setHorizontalHeaderLabels(["Blueprint ID", "Name", "Products"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        results_layout.addWidget(self.results_table)
        
        splitter.addWidget(results_widget)
        
        # Blueprint details section
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 10, 0, 0)
        
        details_label = QLabel("Blueprint Details")
        details_label.setFont(QFont(details_label.font().family(), 10, QFont.Bold))
        details_layout.addWidget(details_label)
        
        # Create a tab widget for different details views
        self.details_tabs = QTabWidget()
        
        # Overview tab
        self.overview_tab = QWidget()
        overview_layout = QFormLayout(self.overview_tab)
        self.blueprint_name_label = QLabel("-")
        self.blueprint_id_label = QLabel("-")
        self.max_runs_label = QLabel("-")
        overview_layout.addRow("Blueprint Name:", self.blueprint_name_label)
        overview_layout.addRow("Blueprint ID:", self.blueprint_id_label)
        overview_layout.addRow("Max Production Limit:", self.max_runs_label)
        self.details_tabs.addTab(self.overview_tab, "Overview")
        
        # Products tab
        self.products_tab = QWidget()
        products_layout = QVBoxLayout(self.products_tab)
        self.products_table = QTableWidget(0, 3)  # columns: ID, Name, Quantity
        self.products_table.setHorizontalHeaderLabels(["Product ID", "Name", "Quantity"])
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        products_layout.addWidget(self.products_table)
        self.details_tabs.addTab(self.products_tab, "Products")
        
        # Materials tab
        self.materials_tab = QWidget()
        materials_layout = QVBoxLayout(self.materials_tab)
        self.materials_table = QTableWidget(0, 3)  # columns: ID, Name, Quantity
        self.materials_table.setHorizontalHeaderLabels(["Material ID", "Name", "Quantity"])
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setEditTriggers(QTableWidget.NoEditTriggers)
        materials_layout.addWidget(self.materials_table)
        self.details_tabs.addTab(self.materials_tab, "Materials")
        
        # Activities tab
        self.activities_tab = QWidget()
        activities_layout = QVBoxLayout(self.activities_tab)
        self.activities_table = QTableWidget(0, 2)  # columns: Activity, Time
        self.activities_table.setHorizontalHeaderLabels(["Activity", "Time (seconds)"])
        self.activities_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.activities_table.verticalHeader().setVisible(False)
        self.activities_table.setEditTriggers(QTableWidget.NoEditTriggers)
        activities_layout.addWidget(self.activities_table)
        self.details_tabs.addTab(self.activities_tab, "Activities")
        
        details_layout.addWidget(self.details_tabs)
        
        splitter.addWidget(details_widget)
        
        # Set initial splitter sizes (40% for results, 60% for details)
        splitter.setSizes([400, 600])
        
        # Status section
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Connect search button to search action
        self.search_button.clicked.connect(self.search_blueprints)
        
        # Connect Enter key in search input to search action
        self.search_input.returnPressed.connect(self.search_blueprints)
        
        # Connect blueprint selection to show details
        self.results_table.itemSelectionChanged.connect(self.show_blueprint_details)
    
    @Slot()
    def search_blueprints(self):
        """Search for blueprints based on the current criteria."""
        query = self.search_input.text().strip()
        activity = self.activity_combo.currentData()
        limit = self.limit_spin.value()
        
        self.status_label.setText(f"Searching for blueprints matching '{query}'...")
        
        try:
            # Get blueprints from search service
            blueprints = self.search_service.search_blueprints(
                query=query,
                activity_name=activity,
                limit=limit
            )
            
            # Update the results table
            self._update_results_table(blueprints)
            
            self.status_label.setText(f"Found {len(blueprints)} blueprints matching '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching for blueprints: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _update_results_table(self, blueprints: List[Blueprint]):
        """
        Update the results table with the blueprint data.
        
        Args:
            blueprints: List of Blueprint objects to display
        """
        # Clear the table
        self.results_table.setRowCount(0)
        
        for blueprint in blueprints:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # Set ID
            id_item = QTableWidgetItem(str(blueprint.id))
            id_item.setData(Qt.UserRole, blueprint.id)  # Store the actual ID for later use
            self.results_table.setItem(row, 0, id_item)
            
            # Set Name
            self.results_table.setItem(row, 1, QTableWidgetItem(blueprint.name))
            
            # Set Products - get the product names for this blueprint
            products = self.db.query(BlueprintProduct).filter_by(blueprint_id=blueprint.id).all()
            product_names = []
            for product in products:
                item = self.db.query(Item).filter_by(id=product.product_id).first()
                if item:
                    product_names.append(f"{item.name} ({product.quantity})")
            
            self.results_table.setItem(row, 2, QTableWidgetItem(", ".join(product_names)))
        
        # Resize columns to contents
        self.results_table.resizeColumnsToContents()
    
    @Slot()
    def show_blueprint_details(self):
        """Show details for the selected blueprint."""
        # Get the selected row
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            logger.debug("No items selected in the results table")
            return
        
        # Get the blueprint ID from the first column
        row = selected_items[0].row()
        blueprint_id_item = self.results_table.item(row, 0)
        blueprint_id = blueprint_id_item.data(Qt.UserRole)
        logger.debug(f"Selected blueprint ID: {blueprint_id}")
        
        try:
            # Get the blueprint from the database
            blueprint = self.db.query(Blueprint).filter_by(id=blueprint_id).first()
            if not blueprint:
                logger.error(f"Blueprint with ID {blueprint_id} not found in database")
                self.status_label.setText(f"Error: Blueprint with ID {blueprint_id} not found")
                return
            
            logger.debug(f"Found blueprint: {blueprint.name} (ID: {blueprint.id})")
            
            # Update overview tab
            self.blueprint_name_label.setText(blueprint.name)
            self.blueprint_id_label.setText(str(blueprint.id))
            self.max_runs_label.setText(str(blueprint.max_production_limit))
            logger.debug("Overview tab updated")
            
            # Update products tab
            self._update_products_table(blueprint_id)
            logger.debug("Products tab updated")
            
            # Update materials tab
            self._update_materials_table(blueprint_id)
            logger.debug("Materials tab updated")
            
            # Update activities tab
            self._update_activities_table(blueprint_id)
            logger.debug("Activities tab updated")
            
            # Ensure the UI is refreshed
            self.details_tabs.repaint()
            
            # Force the current tab to refresh
            current_index = self.details_tabs.currentIndex()
            self.details_tabs.setCurrentIndex((current_index + 1) % self.details_tabs.count())
            self.details_tabs.setCurrentIndex(current_index)
            
            self.status_label.setText(f"Showing details for {blueprint.name}")
            
        except Exception as e:
            logger.error(f"Error showing blueprint details: {e}", exc_info=True)
            self.status_label.setText(f"Error: {str(e)}")
    
    def _update_products_table(self, blueprint_id: int):
        """
        Update the products table for the specified blueprint.
        
        Args:
            blueprint_id: ID of the blueprint
        """
        logger.debug(f"Updating products table for blueprint ID: {blueprint_id}")
        
        # Clear the table
        self.products_table.setRowCount(0)
        self.products_table.clearContents()
        
        # Get products for this blueprint
        products = self.db.query(BlueprintProduct).filter_by(blueprint_id=blueprint_id).all()
        logger.debug(f"Found {len(products)} products for blueprint ID: {blueprint_id}")
        
        for product in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            
            # Set Product ID
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.product_id)))
            
            # Set Product Name
            item = self.db.query(Item).filter_by(id=product.product_id).first()
            name = item.name if item else "Unknown"
            self.products_table.setItem(row, 1, QTableWidgetItem(name))
            
            # Set Quantity
            self.products_table.setItem(row, 2, QTableWidgetItem(str(product.quantity)))
            
            logger.debug(f"Added product: {name} (ID: {product.product_id}, Quantity: {product.quantity})")
        
        # Resize columns to contents
        self.products_table.resizeColumnsToContents()
        
        # Force the table to update
        self.products_table.viewport().update()
    
    def _update_materials_table(self, blueprint_id: int):
        """
        Update the materials table for the specified blueprint.
        
        Args:
            blueprint_id: ID of the blueprint
        """
        logger.debug(f"Updating materials table for blueprint ID: {blueprint_id}")
        
        # Clear the table
        self.materials_table.setRowCount(0)
        self.materials_table.clearContents()
        
        # Get materials for this blueprint
        materials = self.db.query(BlueprintMaterial).filter_by(blueprint_id=blueprint_id).all()
        logger.debug(f"Found {len(materials)} materials for blueprint ID: {blueprint_id}")
        
        for material in materials:
            row = self.materials_table.rowCount()
            self.materials_table.insertRow(row)
            
            # Set Material ID
            self.materials_table.setItem(row, 0, QTableWidgetItem(str(material.material_id)))
            
            # Set Material Name
            item = self.db.query(Item).filter_by(id=material.material_id).first()
            name = item.name if item else "Unknown"
            self.materials_table.setItem(row, 1, QTableWidgetItem(name))
            
            # Set Quantity
            self.materials_table.setItem(row, 2, QTableWidgetItem(str(material.quantity)))
            
            logger.debug(f"Added material: {name} (ID: {material.material_id}, Quantity: {material.quantity})")
        
        # Resize columns to contents
        self.materials_table.resizeColumnsToContents()
        
        # Force the table to update
        self.materials_table.viewport().update()
    
    def _update_activities_table(self, blueprint_id: int):
        """
        Update the activities table for the specified blueprint.
        
        Args:
            blueprint_id: ID of the blueprint
        """
        logger.debug(f"Updating activities table for blueprint ID: {blueprint_id}")
        
        # Clear the table
        self.activities_table.setRowCount(0)
        self.activities_table.clearContents()
        
        # Get activities for this blueprint
        activities = self.db.query(BlueprintActivity).filter_by(blueprint_id=blueprint_id).all()
        logger.debug(f"Found {len(activities)} activities for blueprint ID: {blueprint_id}")
        
        for activity in activities:
            row = self.activities_table.rowCount()
            self.activities_table.insertRow(row)
            
            # Set Activity Name
            self.activities_table.setItem(row, 0, QTableWidgetItem(activity.activity_name))
            
            # Set Time
            self.activities_table.setItem(row, 1, QTableWidgetItem(str(activity.time)))
            
            logger.debug(f"Added activity: {activity.activity_name} (Time: {activity.time})")
        
        # Resize columns to contents
        self.activities_table.resizeColumnsToContents()
        
        # Force the table to update
        self.activities_table.viewport().update() 