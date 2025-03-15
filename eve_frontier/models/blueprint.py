"""
Blueprint model for EVE Frontier Blueprint Miracle.

This module defines the Blueprint SQLAlchemy model class for representing EVE Online blueprints.
"""

from typing import List, Optional

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from eve_frontier.models.base import Base


class Blueprint(Base):
    """Model representing a blueprint in EVE Online."""
    
    __tablename__ = "blueprints"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    max_production_limit = Column(Integer, default=0)
    
    # Relationships
    products = relationship("BlueprintProduct", back_populates="blueprint")
    materials = relationship("BlueprintMaterial", back_populates="blueprint")
    
    def __repr__(self) -> str:
        return f"<Blueprint id={self.id} name={self.name}>"


class BlueprintProduct(Base):
    """Model representing a product produced by a blueprint."""
    
    __tablename__ = "blueprint_products"
    
    id = Column(Integer, primary_key=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.id"), index=True)
    product_id = Column(Integer, ForeignKey("items.id"), index=True)
    quantity = Column(Integer, default=1)
    
    # Relationships
    blueprint = relationship("Blueprint", back_populates="products")
    product = relationship("Item", back_populates="blueprints_as_product")
    
    def __repr__(self) -> str:
        return f"<BlueprintProduct blueprint_id={self.blueprint_id} product_id={self.product_id}>"


class BlueprintMaterial(Base):
    """Model representing a material required for a blueprint."""
    
    __tablename__ = "blueprint_materials"
    
    id = Column(Integer, primary_key=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.id"), index=True)
    material_id = Column(Integer, ForeignKey("items.id"), index=True)
    quantity = Column(Integer, default=1)
    
    # Relationships
    blueprint = relationship("Blueprint", back_populates="materials")
    material = relationship("Item", back_populates="blueprints_as_material")
    
    def __repr__(self) -> str:
        return f"<BlueprintMaterial blueprint_id={self.blueprint_id} material_id={self.material_id}>"


class BlueprintActivity(Base):
    """Model representing an activity that can be performed with a blueprint."""
    
    __tablename__ = "blueprint_activities"
    
    id = Column(Integer, primary_key=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.id"), index=True)
    activity_name = Column(String, nullable=False)  # e.g., "manufacturing", "copying", "research"
    time = Column(Integer, default=0)  # Time in seconds
    
    # Relationships
    blueprint = relationship("Blueprint")
    
    def __repr__(self) -> str:
        return f"<BlueprintActivity blueprint_id={self.blueprint_id} activity={self.activity_name}>"


class SkillRequirement(Base):
    """Model representing a skill required for a blueprint activity."""
    
    __tablename__ = "skill_requirements"
    
    id = Column(Integer, primary_key=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.id"), index=True)
    activity_id = Column(Integer, ForeignKey("blueprint_activities.id"), index=True, nullable=True)
    skill_id = Column(Integer, ForeignKey("items.id"), index=True)
    level = Column(Integer, default=1)
    
    # Relationships
    blueprint = relationship("Blueprint")
    activity = relationship("BlueprintActivity")
    skill = relationship("Item")
    
    def __repr__(self) -> str:
        return f"<SkillRequirement blueprint_id={self.blueprint_id} skill_id={self.skill_id} level={self.level}>" 