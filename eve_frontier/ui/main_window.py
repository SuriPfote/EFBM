#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE Frontier Blueprint Miracle - Main Window

This module defines the main application window and its components.
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QToolBar, 
    QVBoxLayout, QWidget, QMessageBox,
    QLabel, QHBoxLayout, QMenuBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

logger = logging.getLogger("main_window")

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("EVE Frontier Blueprint Miracle")
        self.setMinimumSize(1024, 768)
        
        # Initialize UI components
        self._init_ui()
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Add placeholder tabs
        self._create_tabs()
        
        logger.debug("UI components initialized")
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        
        # Add actions to File menu
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        
        # Tools menu
        self.tools_menu = self.menuBar().addMenu("&Tools")
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("About EVE Frontier Blueprint Miracle")
        about_action.triggered.connect(self._show_about_dialog)
        self.help_menu.addAction(about_action)
        
        logger.debug("Menu bar created")
    
    def _create_tabs(self):
        """Create the main application tabs."""
        # Import tab classes here to avoid circular imports
        from eve_frontier.ui.tabs import BlueprintBrowserTab
        from eve_frontier.ui.tabs.production_chain import ProductionChainTab
        from eve_frontier.ui.tabs.market_data import MarketDataTab
        from eve_frontier.models.base import get_db
        
        # Get a database session
        db = get_db()
        
        # Create Blueprint Browser tab
        self.blueprint_browser_tab = BlueprintBrowserTab(db)
        self.tab_widget.addTab(self.blueprint_browser_tab, "Blueprint Browser")
        
        # Create Production Chain tab
        self.production_chain_tab = ProductionChainTab(db)
        self.tab_widget.addTab(self.production_chain_tab, "Production Chain")
        
        # Create Market Data tab
        self.market_data_tab = MarketDataTab(db)
        self.tab_widget.addTab(self.market_data_tab, "Market Data")
        
        logger.debug("Tabs created")
    
    def _create_item_search_tab(self):
        """Create the item search tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add a label explaining this is a placeholder
        label = QLabel("Item Search Tab - Placeholder")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Add a description
        description = QLabel(
            "This tab will allow searching for items, blueprints, and materials.\n"
            "The search results will display detailed information about the selected items."
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        self.tab_widget.addTab(tab, "Item Search")
    
    def _show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About EVE Frontier Blueprint Miracle",
            """
            <h1>EVE Frontier Blueprint Miracle</h1>
            <p>Version 0.1.0</p>
            <p>A tool for analyzing EVE Online blueprints and optimizing production chains.</p>
            <p>&copy; 2025 EVE Frontier</p>
            <p>EVE Online and all related trademarks are the property of CCP Games.</p>
            """
        )
        logger.debug("About dialog shown") 