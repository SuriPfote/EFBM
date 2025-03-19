"""
Production Chain Tab for EVE Frontier Blueprint Miracle.

This module defines the Production Chain tab which allows users to analyze production chains,
calculate material requirements, and estimate production costs.
"""

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal

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

from eve_frontier.models import Item, Blueprint, BlueprintMaterial
from eve_frontier.services.search_service import SearchService
from eve_frontier.services.production_service import ProductionService, ProductionChainNode
from eve_frontier.services.market_service import MarketService

logger = logging.getLogger(__name__)

class ProductionChainTab(QWidget):
    """Production Chain tab for analyzing item manufacturing chains."""
    
    def __init__(self, db: Session):
        """
        Initialize the Production Chain tab.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__()
        
        # Initialize services
        self.db = db
        self.search_service = SearchService(db)
        self.production_service = ProductionService(db)
        self.market_service = MarketService(db)
        
        # Store current production chain
        self.current_chain: Optional[ProductionChainNode] = None
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals to slots
        self._connect_signals()
        
        logger.info("Production Chain tab initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create item selection section
        item_selection_group = QGroupBox("Select Item to Manufacture")
        item_selection_layout = QVBoxLayout(item_selection_group)
        
        # Item search row
        item_search_layout = QHBoxLayout()
        self.item_search_input = QLineEdit()
        self.item_search_input.setPlaceholderText("Enter item name to manufacture...")
        self.item_search_button = QPushButton("Search")
        self.item_search_button.setFixedWidth(100)
        item_search_layout.addWidget(self.item_search_input)
        item_search_layout.addWidget(self.item_search_button)
        item_selection_layout.addLayout(item_search_layout)
        
        # Item results
        self.item_results_table = QTableWidget(0, 3)  # columns: ID, Name, Category
        self.item_results_table.setHorizontalHeaderLabels(["Item ID", "Name", "Category"])
        self.item_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.item_results_table.verticalHeader().setVisible(False)
        self.item_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.item_results_table.setMaximumHeight(150)
        item_selection_layout.addWidget(self.item_results_table)
        
        # Production options
        options_layout = QHBoxLayout()
        
        # Quantity
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantity:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSingleStep(1)
        quantity_layout.addWidget(self.quantity_spin)
        options_layout.addLayout(quantity_layout)
        
        # Material efficiency level
        me_layout = QHBoxLayout()
        me_layout.addWidget(QLabel("ME Level:"))
        self.me_level_spin = QSpinBox()
        self.me_level_spin.setRange(0, 10)
        self.me_level_spin.setValue(0)
        me_layout.addWidget(self.me_level_spin)
        options_layout.addLayout(me_layout)
        
        # Time efficiency level
        te_layout = QHBoxLayout()
        te_layout.addWidget(QLabel("TE Level:"))
        self.te_level_spin = QSpinBox()
        self.te_level_spin.setRange(0, 20)
        self.te_level_spin.setValue(0)
        te_layout.addWidget(self.te_level_spin)
        options_layout.addLayout(te_layout)
        
        # Facility bonus
        facility_layout = QHBoxLayout()
        facility_layout.addWidget(QLabel("Facility Bonus:"))
        self.facility_combo = QComboBox()
        self.facility_combo.addItem("None", 0.0)
        self.facility_combo.addItem("Station (0%)", 0.0)
        self.facility_combo.addItem("Engineering Complex (15%)", 0.15)
        self.facility_combo.addItem("Manufacturing Complex (25%)", 0.25)
        facility_layout.addWidget(self.facility_combo)
        options_layout.addLayout(facility_layout)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate Production Chain")
        self.calculate_button.setEnabled(False)
        options_layout.addWidget(self.calculate_button)
        
        item_selection_layout.addLayout(options_layout)
        
        # Add item selection section to main layout
        main_layout.addWidget(item_selection_group)
        
        # Create a splitter for production chain and details
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)
        
        # Production chain section
        chain_widget = QWidget()
        chain_layout = QVBoxLayout(chain_widget)
        chain_layout.setContentsMargins(0, 10, 0, 0)
        
        chain_header = QLabel("Production Chain")
        chain_header.setFont(QFont(chain_header.font().family(), 10, QFont.Bold))
        chain_layout.addWidget(chain_header)
        
        # Tree view for production chain
        self.chain_tree = QTreeWidget()
        self.chain_tree.setHeaderLabels(["Item", "Quantity", "Time", "Cost"])
        self.chain_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        chain_layout.addWidget(self.chain_tree)
        
        splitter.addWidget(chain_widget)
        
        # Material summary section
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 10, 0, 0)
        
        # Create tabs for different views
        self.details_tabs = QTabWidget()
        
        # Materials tab
        self.materials_tab = QWidget()
        materials_layout = QVBoxLayout(self.materials_tab)
        self.materials_table = QTableWidget(0, 4)  # columns: ID, Name, Quantity, Cost
        self.materials_table.setHorizontalHeaderLabels(["Material ID", "Name", "Quantity", "Cost"])
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setEditTriggers(QTableWidget.NoEditTriggers)
        materials_layout.addWidget(self.materials_table)
        self.details_tabs.addTab(self.materials_tab, "Raw Materials")
        
        # Cost tab
        self.cost_tab = QWidget()
        cost_layout = QFormLayout(self.cost_tab)
        self.total_cost_label = QLabel("0.00 ISK")
        self.material_cost_label = QLabel("0.00 ISK")
        self.production_time_label = QLabel("0 seconds")
        self.profit_margin_label = QLabel("0.00 ISK")
        self.profit_per_hour_label = QLabel("0.00 ISK/hr")
        cost_layout.addRow("Total Cost:", self.total_cost_label)
        cost_layout.addRow("Material Cost:", self.material_cost_label)
        cost_layout.addRow("Production Time:", self.production_time_label)
        cost_layout.addRow("Profit Margin:", self.profit_margin_label)
        cost_layout.addRow("Profit per Hour:", self.profit_per_hour_label)
        self.details_tabs.addTab(self.cost_tab, "Cost Analysis")
        
        summary_layout.addWidget(self.details_tabs)
        
        splitter.addWidget(summary_widget)
        
        # Set initial splitter sizes (60% for chain, 40% for summary)
        splitter.setSizes([600, 400])
        
        # Status section
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Connect search button to search action
        self.item_search_button.clicked.connect(self.search_items)
        
        # Connect Enter key in search input to search action
        self.item_search_input.returnPressed.connect(self.search_items)
        
        # Connect item selection to enable calculate button
        self.item_results_table.itemSelectionChanged.connect(self._enable_calculate)
        
        # Connect calculate button to calculate action
        self.calculate_button.clicked.connect(self.calculate_production_chain)
        
        # Connect tree selection to update material details
        self.chain_tree.itemSelectionChanged.connect(self._update_material_details)
    
    @Slot()
    def _enable_calculate(self):
        """Enable calculate button when an item is selected."""
        self.calculate_button.setEnabled(self.item_results_table.selectedItems() != [])
    
    @Slot()
    def search_items(self):
        """Search for items based on the current criteria."""
        query = self.item_search_input.text().strip()
        
        logger.debug(f"Starting item search with query: '{query}'")
        self.status_label.setText(f"Searching for items matching '{query}'...")
        
        try:
            # Get items from search service
            logger.debug("Calling search_service.search_items")
            items = self.search_service.search_items(
                query=query,
                limit=10  # Limit to 10 results for simplicity
            )
            logger.debug(f"Found {len(items)} items: {[item.name for item in items]}")
            
            # Update the results table
            logger.debug("Updating item results table")
            self._update_item_results_table(items)
            
            self.status_label.setText(f"Found {len(items)} items matching '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching for items: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.status_label.setText(f"Error: {str(e)}")
    
    def _update_item_results_table(self, items: List[Item]):
        """
        Update the results table with the item data.
        
        Args:
            items: List of Item objects to display
        """
        # Clear the table
        self.item_results_table.setRowCount(0)
        
        for item in items:
            row = self.item_results_table.rowCount()
            self.item_results_table.insertRow(row)
            
            # Item ID
            id_item = QTableWidgetItem(str(item.id))
            self.item_results_table.setItem(row, 0, id_item)
            
            # Item Name
            name_item = QTableWidgetItem(item.name)
            self.item_results_table.setItem(row, 1, name_item)
            
            # Category (via group relationship)
            category_name = item.group.category.name if item.group and item.group.category else "Unknown"
            category_item = QTableWidgetItem(category_name)
            self.item_results_table.setItem(row, 2, category_item)
    
    @Slot()
    def calculate_production_chain(self):
        """Calculate the production chain for the selected item."""
        # Get the selected item
        selected_items = self.item_results_table.selectedItems()
        if not selected_items:
            logger.debug("No item selected for production chain calculation")
            return
        
        # Get the item ID from the first column
        item_id = int(self.item_results_table.item(selected_items[0].row(), 0).text())
        item_name = self.item_results_table.item(selected_items[0].row(), 1).text()
        logger.debug(f"Selected item for production chain: {item_name} (ID: {item_id})")
        
        # Get production options
        quantity = self.quantity_spin.value()
        me_level = self.me_level_spin.value()
        te_level = self.te_level_spin.value()
        facility_bonus = self.facility_combo.currentData()
        logger.debug(f"Production options: quantity={quantity}, ME={me_level}, TE={te_level}, facility_bonus={facility_bonus}")
        
        self.status_label.setText(f"Calculating production chain for {item_name}...")
        
        try:
            # Get manufacturing details
            logger.debug(f"Calling production_service.get_manufacturing_details for item_id={item_id}")
            self.current_chain = self.production_service.get_manufacturing_details(
                item_id=item_id,
                quantity=quantity,
                me_level=me_level,
                te_level=te_level,
                facility_bonus=facility_bonus,
                max_depth=5  # Go 5 levels deep
            )
            
            if self.current_chain:
                logger.debug(f"Retrieved production chain: {self.current_chain.item_name} with {len(self.current_chain.materials)} materials")
                # Update the production chain tree
                logger.debug("Updating production chain tree")
                self._update_production_chain_tree()
                
                # Update the raw materials table
                logger.debug("Updating raw materials table")
                self._update_raw_materials_table()
                
                # Update the cost analysis
                logger.debug("Updating cost analysis")
                self._update_cost_analysis()
                
                self.status_label.setText(f"Production chain calculated for {quantity}x {item_name}")
            else:
                logger.warning(f"No production chain found for item_id={item_id} ({item_name})")
                self.status_label.setText(f"No production chain found for {item_name}")
                
        except Exception as e:
            logger.error(f"Error calculating production chain: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.status_label.setText(f"Error: {str(e)}")
    
    def _update_production_chain_tree(self):
        """Update the production chain tree with the current chain."""
        # Clear the tree
        self.chain_tree.clear()
        
        if not self.current_chain:
            return
        
        # Create the root item
        root_item = QTreeWidgetItem([
            self.current_chain.item_name,
            str(self.current_chain.quantity),
            self._format_time(self.current_chain.time_required) if self.current_chain.time_required else "N/A",
            f"{self.current_chain.production_cost:.2f} ISK" if self.current_chain.production_cost else "N/A"
        ])
        self.chain_tree.addTopLevelItem(root_item)
        
        # Add child nodes recursively
        self._add_child_nodes(root_item, self.current_chain.materials)
        
        # Expand the root item
        root_item.setExpanded(True)
    
    def _add_child_nodes(self, parent_item: QTreeWidgetItem, materials: List[ProductionChainNode]):
        """
        Add child nodes to the production chain tree.
        
        Args:
            parent_item: Parent QTreeWidgetItem
            materials: List of ProductionChainNode objects to add as children
        """
        for material in materials:
            # Create the child item
            child_item = QTreeWidgetItem([
                material.item_name,
                str(material.quantity),
                self._format_time(material.time_required) if material.time_required else "N/A",
                f"{material.production_cost:.2f} ISK" if material.production_cost else "N/A"
            ])
            parent_item.addChild(child_item)
            
            # Add grandchildren recursively
            self._add_child_nodes(child_item, material.materials)
    
    def _update_raw_materials_table(self):
        """Update the raw materials table with the current chain's base materials."""
        # Clear the table
        self.materials_table.setRowCount(0)
        
        if not self.current_chain:
            return
        
        # Extract all raw materials (items with no materials of their own)
        raw_materials = self._extract_raw_materials(self.current_chain)
        
        # Sort by name
        raw_materials.sort(key=lambda x: x[0])
        
        for material_name, material_id, total_quantity, cost in raw_materials:
            row = self.materials_table.rowCount()
            self.materials_table.insertRow(row)
            
            # Material ID
            id_item = QTableWidgetItem(str(material_id))
            self.materials_table.setItem(row, 0, id_item)
            
            # Material Name
            name_item = QTableWidgetItem(material_name)
            self.materials_table.setItem(row, 1, name_item)
            
            # Quantity
            quantity_item = QTableWidgetItem(str(total_quantity))
            quantity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.materials_table.setItem(row, 2, quantity_item)
            
            # Cost
            cost_item = QTableWidgetItem(f"{cost:.2f} ISK" if cost is not None else "N/A")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.materials_table.setItem(row, 3, cost_item)
    
    def _extract_raw_materials(self, node: ProductionChainNode) -> List[tuple]:
        """
        Extract all raw materials from a production chain.
        
        Args:
            node: ProductionChainNode to extract materials from
            
        Returns:
            List of tuples (material_name, material_id, quantity, cost)
        """
        if not node:
            return []
        
        # If this node has no materials, it's a raw material
        if not node.materials:
            # Ensure cost is calculated consistently
            cost = None
            if hasattr(node, 'buy_price') and node.buy_price is not None:
                # Calculate total cost based on quantity
                cost = node.buy_price * node.quantity
            
            # Return as a single-item list
            return [(node.item_name, node.item_id, node.quantity, cost)]
        
        # Otherwise, extract materials from all children
        result = []
        for material in node.materials:
            result.extend(self._extract_raw_materials(material))
        
        # Combine like materials
        combined = {}
        for name, id, quantity, cost in result:
            if id not in combined:
                combined[id] = [name, id, 0, None]
            
            # Add quantities
            combined[id][2] += quantity
            
            # Handle cost combining with type consistency
            if cost is not None:
                if combined[id][3] is None:
                    combined[id][3] = cost
                else:
                    # If either value is Decimal, convert both to Decimal for consistent math
                    if isinstance(cost, Decimal) or isinstance(combined[id][3], Decimal):
                        # Convert to Decimal if needed
                        if not isinstance(combined[id][3], Decimal):
                            combined[id][3] = Decimal(str(combined[id][3]))
                        if not isinstance(cost, Decimal):
                            cost = Decimal(str(cost))
                        
                    # Add the values using appropriate type
                    combined[id][3] += cost
        
        return list(combined.values())
    
    def _update_cost_analysis(self):
        """Update the cost analysis tab with the current chain's cost information."""
        if not self.current_chain:
            self.total_cost_label.setText("0.00 ISK")
            self.material_cost_label.setText("0.00 ISK")
            self.production_time_label.setText("0 seconds")
            self.profit_margin_label.setText("0.00 ISK")
            self.profit_per_hour_label.setText("0.00 ISK/hr")
            return
        
        # Calculate total material cost
        raw_materials = self._extract_raw_materials(self.current_chain)
        material_cost = sum(cost for _, _, _, cost in raw_materials if cost is not None)
        
        # Get total production time (recursive)
        production_time = self._calculate_total_time(self.current_chain)
        
        # Calculate market value (placeholder)
        market_value = self.current_chain.sell_price * self.current_chain.quantity if self.current_chain.sell_price else 0
        
        # Calculate profit
        profit = market_value - material_cost
        
        # Calculate profit per hour
        profit_per_hour = (profit / (production_time / 3600)) if production_time > 0 else 0
        
        # Update labels
        self.total_cost_label.setText(f"{material_cost:.2f} ISK")
        self.material_cost_label.setText(f"{material_cost:.2f} ISK")
        self.production_time_label.setText(self._format_time(production_time))
        self.profit_margin_label.setText(f"{profit:.2f} ISK")
        self.profit_per_hour_label.setText(f"{profit_per_hour:.2f} ISK/hr")
    
    def _calculate_total_time(self, node: ProductionChainNode) -> int:
        """
        Calculate the total production time for a chain (in seconds).
        
        Args:
            node: ProductionChainNode to calculate time for
            
        Returns:
            Total time in seconds
        """
        if not node:
            return 0
        
        # Base time for this node
        base_time = node.time_required or 0
        
        # For parallel manufacturing, we take the max time of child nodes
        # This is a simplified model; in reality, you might have complex dependency trees
        child_time = max([self._calculate_total_time(material) for material in node.materials], default=0)
        
        # Return total time (current node + longest child path)
        return base_time + child_time
    
    @Slot()
    def _update_material_details(self):
        """Update material details based on the selected node in the tree."""
        # This method would show detailed information about the selected material
        # including market prices, alternative blueprints, etc.
        # Placeholder for future implementation
        pass
    
    def _format_time(self, seconds: Optional[int]) -> str:
        """
        Format time in seconds to a readable string.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds is None:
            return "N/A"
        
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"