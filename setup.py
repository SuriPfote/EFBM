#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EVE Frontier Blueprint Miracle - Package Setup

This script sets up the EVE Frontier Blueprint Miracle package for installation.
"""

from setuptools import setup, find_packages

setup(
    name="eve-frontier-blueprint-miracle",
    version="0.1.0",
    description="A tool for analyzing EVE Online blueprints and production chains",
    author="EVE Frontier",
    author_email="info@evefrontier.org",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.4.0",
        "SQLAlchemy>=2.0.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "numpy>=1.24.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "eve-frontier=eve_frontier.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
    ],
) 