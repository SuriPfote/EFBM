#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE Frontier Blueprint Miracle - Main Application

This is the main entry point for the EVE Frontier Blueprint Miracle application.
It initializes the application, loads configuration, and creates the main window.
"""

import sys
import os
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream, QCoreApplication

# Set application metadata
QCoreApplication.setOrganizationName("EVE Frontier")
QCoreApplication.setOrganizationDomain("evefrontier.org")
QCoreApplication.setApplicationName("Blueprint Miracle")
QCoreApplication.setApplicationVersion("0.1.0")

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

def load_stylesheet():
    """Load the application stylesheet."""
    # Placeholder for actual stylesheet loading
    logger.info("Loading application stylesheet")
    return """
    QMainWindow {
        background-color: #2d2d30;
        color: #f0f0f0;
    }
    QTabWidget {
        background-color: #2d2d30;
    }
    QTabBar::tab {
        background-color: #3e3e42;
        color: #f0f0f0;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background-color: #0078d7;
    }
    QStatusBar {
        background-color: #1e1e1e;
        color: #f0f0f0;
    }
    QToolBar {
        background-color: #2d2d30;
        border: none;
    }
    QMenuBar {
        background-color: #2d2d30;
        color: #f0f0f0;
    }
    QMenuBar::item:selected {
        background-color: #3e3e42;
    }
    QMenu {
        background-color: #2d2d30;
        color: #f0f0f0;
        border: 1px solid #3e3e42;
    }
    QMenu::item:selected {
        background-color: #3e3e42;
    }
    """

def main():
    """Main application entry point."""
    logger.info("Starting EVE Frontier Blueprint Miracle")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Apply stylesheet
    app.setStyleSheet(load_stylesheet())
    
    # Import here to avoid circular imports
    try:
        from eve_frontier.ui.main_window import MainWindow
        logger.info("Creating main application window")
        window = MainWindow()
        window.show()
    except ImportError as e:
        logger.error(f"Failed to import main window: {e}")
        from PySide6.QtWidgets import QMessageBox
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setText("Failed to start the application")
        error_box.setInformativeText(
            f"Error importing components: {str(e)}\n\n"
            "This might be due to a missing dependency or incorrect installation."
        )
        error_box.setWindowTitle("Application Error")
        error_box.exec()
        return 1
    
    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 