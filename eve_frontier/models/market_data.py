"""
Market Data model for EVE Frontier Blueprint Miracle.

This module defines the MarketData SQLAlchemy model class for representing EVE Online market data.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from eve_frontier.models.base import Base


class Station(Base):
    """Model representing a station in EVE Online."""
    
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    region = Column(String, nullable=True)
    
    # Relationships
    market_data = relationship("MarketData", back_populates="station")
    
    def __repr__(self) -> str:
        return f"<Station id={self.id} name={self.name}>"


class TradingHub(Base):
    """Model representing a trading hub in EVE Online."""
    
    __tablename__ = "trading_hubs"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    system_id = Column(Integer, nullable=False)
    region_id = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    
    def __repr__(self) -> str:
        return f"<TradingHub id={self.id} name={self.name}>"


class MarketData(Base):
    """Model representing market data for an item in EVE Online."""
    
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), index=True)
    buy_price = Column(Float, nullable=True)
    sell_price = Column(Float, nullable=True)
    buy_volume = Column(Integer, nullable=True)
    sell_volume = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    item = relationship("Item")
    station = relationship("Station", back_populates="market_data")
    
    def __repr__(self) -> str:
        return f"<MarketData item_id={self.item_id} station_id={self.station_id}>"


class MarketOrderType:
    """Enum-like class for market order types."""
    BUY = "buy"
    SELL = "sell"


class MarketOrder(Base):
    """Model representing a market order in EVE Online."""
    
    __tablename__ = "market_orders"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), index=True)
    order_type = Column(String, index=True)  # "buy" or "sell"
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    min_volume = Column(Integer, nullable=True)
    range_str = Column(String, nullable=True)  # Range as a string (e.g., "station", "region", "5")
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    item = relationship("Item")
    station = relationship("Station")
    
    def __repr__(self) -> str:
        return f"<MarketOrder item_id={self.item_id} type={self.order_type} price={self.price}>"


class MarketHistory(Base):
    """Model representing historical market data for an item in EVE Online."""
    
    __tablename__ = "market_history"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), index=True)
    region_id = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    average_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Relationships
    item = relationship("Item")
    
    def __repr__(self) -> str:
        return f"<MarketHistory item_id={self.item_id} date={self.date}>" 