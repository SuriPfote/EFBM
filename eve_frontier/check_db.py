#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to check the database.
"""

import logging
from models.base import get_db
from models import Blueprint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_db")

# Get a database session
db = get_db()

try:
    # Check if there are any blueprints with "steel" in their name
    blueprints = db.query(Blueprint).filter(Blueprint.name.ilike('%steel%')).all()
    
    logger.info(f"Found {len(blueprints)} blueprints with 'steel' in their name:")
    for blueprint in blueprints:
        logger.info(f"  ID: {blueprint.id}, Name: {blueprint.name}")
    
    # Check the first 10 blueprint names
    blueprints = db.query(Blueprint).limit(10).all()
    
    logger.info("First 10 blueprint names:")
    for blueprint in blueprints:
        logger.info(f"  ID: {blueprint.id}, Name: {blueprint.name}")

except Exception as e:
    logger.error(f"Error checking blueprints: {e}")

finally:
    db.close() 