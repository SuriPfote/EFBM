"""
Base database models for EVE Frontier Blueprint Miracle.

This module defines the SQLAlchemy base classes and database connection.
"""

from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from eve_frontier.config import config

# Create SQLAlchemy engine
engine = create_engine(config.db_url, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Session:
    """
    Get a database session.
    
    Returns:
        A SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine) 