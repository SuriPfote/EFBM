# EVE Frontier Blueprint Miracle - Documentation

## Overview

This directory contains documentation for the EVE Frontier Blueprint Miracle application. These documents serve as a reference for the application's architecture, data structures, features, implementation plan, and test results.

## Repository

The project is hosted on GitHub at [https://github.com/SuriPfote/EFBM](https://github.com/SuriPfote/EFBM).

Key branches:
- `master`: Main development branch
- `foundation`: Stable baseline implementation with core functionality

## Documents

- [Architecture](architecture.md): Describes the high-level architecture of the application
- [Data Structure](data_structure.md): Details the data structures used in the application
- [Features](features.md): Outlines the features and functionality of the application
- [Implementation Plan](implementation_plan.md): Provides a step-by-step approach to building the application
- [Troubleshooting](troubleshooting.md): Outlines common issues and troubleshooting steps
- [Test Results](test_results.md): Summarizes the results of service and model testing
- [Development Roadmap](development_roadmap.md): Outlines the planned development milestones and tasks

## Current State

As of the latest development, the application has the following components implemented:

1. Core service layer (data loading, searching, production analysis, market data)
2. Database models (items, blueprints, market data)
3. Blueprint Browser tab with full search and display functionality
4. GitHub integration with version control

The Blueprint Browser tab implementation includes:
- Blueprint search with filtering by activity type
- Detailed blueprint information display
- Products, materials, and manufacturing activities panels

All services have been tested and verified to work as expected. The next phase of development will continue implementing the user interface components, focusing on the Production Chain tab and Market Data tab.

## Purpose

These documents are intended to serve as a reference for developers working on the EVE Frontier Blueprint Miracle application. They provide a comprehensive overview of the application's design, functionality, and implementation details.

## Usage

When implementing the application, refer to these documents to ensure that the implementation aligns with the intended design and functionality. The documents should be updated as the implementation progresses to reflect any changes or refinements to the design.

## Contributing

When contributing to the application, please ensure that your changes align with the architecture and design principles outlined in these documents. If your changes require modifications to the architecture or design, please update the relevant documents to reflect these changes.

### Git Workflow

The project follows a feature branch workflow:
1. Create feature branches from `master`
2. Make your changes and commit them with descriptive messages
3. Push your branch to GitHub
4. Submit pull requests to merge into `master`
5. Tag significant releases with version numbers

The `foundation` branch preserves the initial baseline implementation and should not be modified.
