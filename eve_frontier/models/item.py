"""
Item model for EVE Frontier Blueprint Miracle.

This module defines the Item SQLAlchemy model class for representing EVE Online items.
"""

from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from eve_frontier.models.base import Base


class Category(Base):
    """Model representing an item category in EVE Online."""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    published = Column(Boolean, default=True)
    
    # Relationships
    groups = relationship("Group", back_populates="category")
    
    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name}>"


class Group(Base):
    """Model representing an item group in EVE Online."""
    
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    published = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("Category", back_populates="groups")
    items = relationship("Item", back_populates="group")
    
    def __repr__(self) -> str:
        return f"<Group id={self.id} name={self.name}>"


class Item(Base):
    """Model representing an item in EVE Online."""
    
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    base_price = Column(Float, default=0.0)
    volume = Column(Float, default=0.0)
    published = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    
    # Relationships
    group = relationship("Group", back_populates="items")
    blueprints_as_product = relationship("BlueprintProduct", back_populates="product")
    blueprints_as_material = relationship("BlueprintMaterial", back_populates="material")
    
    def __repr__(self) -> str:
        return f"<Item id={self.id} name={self.name}>" 