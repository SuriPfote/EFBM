#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to run the profitability analyzer as a standalone tool.
"""

import sys
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("profitability_analyzer_test")

def main():
    """Run the profitability analyzer as a standalone application."""
    # Get path to database
    db_path = "eve_frontier.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    db_path = Path(db_path).resolve()
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        print(f"Error: Database file not found: {db_path}")
        return 1
    
    logger.info(f"Using database: {db_path}")
    
    # Create database connection
    engine_url = f"sqlite:///{db_path}"
    engine = create_engine(engine_url)
    session = Session(engine)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("EVE Frontier - Profitability Analyzer")
    
    # Import here to avoid circular imports
    try:
        from eve_frontier.ui.widgets.profitability_analyzer_widget import ProfitabilityAnalyzerWidget
        
        # Create main window
        window = QMainWindow()
        window.setWindowTitle("EVE Frontier - Profitability Analyzer")
        window.setMinimumSize(1024, 768)
        
        # Set the profitability analyzer as the central widget
        analyzer = ProfitabilityAnalyzerWidget(session)
        window.setCentralWidget(analyzer)
        
        # Show the window
        window.show()
        
        # Auto-start analysis after a short delay (optional)
        QTimer.singleShot(500, analyzer.start_analysis)
        
    except ImportError as e:
        logger.error(f"Error importing components: {e}")
        print(f"Error: {e}")
        return 1
    
    # Run the application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 