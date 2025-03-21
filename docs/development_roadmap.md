# Development Roadmap

This document outlines the development roadmap for the EVE Frontier Blueprint Miracle application, organizing future work into milestones with specific features and tasks.

## Current Status

**Version 0.1.0** (Released: 2025-03-15)
- ✅ Core service layer implemented and tested
- ✅ Database models implemented and tested
- ✅ Basic UI framework with placeholder tabs
- ✅ Package setup for installation
- ✅ GitHub repository setup with foundation branch

## Version Control and Collaboration

- ✅ GitHub repository created at [https://github.com/SuriPfote/EFBM](https://github.com/SuriPfote/EFBM)
- ✅ Foundation branch established to preserve baseline implementation
- ✅ Documentation updated with contribution guidelines
- [ ] Create project wiki with development guidelines
- [ ] Set up GitHub Actions for automated testing
- [ ] Implement issue templates for bug reports and feature requests

## Milestone 1: UI Implementation (Target: v0.2.0)

### Blueprint Browser Tab
- [x] Design and implement blueprint search interface
- [x] Create blueprint results display with details panel
- [x] Implement activity filtering
- [x] Display blueprint products, materials, and activities
- [x] Connect UI to SearchService
- [x] Fix UI refresh issues in detail panels
- [x] Ensure proper database connectivity with absolute paths
- [x] Implement comprehensive error handling and logging

### Production Chain Tab
- [ ] Design and implement blueprint selection interface
- [ ] Create material requirements display
- [ ] Implement production options configuration
- [ ] Design production cost breakdown interface
- [ ] Connect production UI to ProductionService

### Market Data Tab
- [x] Design and implement item selection for market data
- [x] Create price history charts
- [x] Implement trading hub selection and comparison
- [x] Design order book visualization
- [x] Connect market UI to MarketService
- [x] Implement Profitability Analyzer Widget
- [x] Add manufacturing profit calculation and filtering
- [x] Fix error handling in market statistics and production services
- [x] Ensure proper model access patterns in market data processing

### General UI
- [ ] Implement application settings dialog
- [ ] Create about dialog with version information
- [ ] Add toolbar with common actions
- [ ] Implement status bar updates with operation status
- [ ] Create splash screen for startup

## Milestone 2: Data Import and Export (Target: v0.3.0)

### Data Import
- [ ] Implement EVE SDE data import wizard
- [ ] Create manual JSON data import dialog
- [ ] Implement progress tracking for data import
- [ ] Add data validation and error reporting
- [ ] Design database update mechanism

### Data Export
- [ ] Implement production plan export to CSV/Excel
- [ ] Create market data export functionality
- [ ] Design blueprint library export
- [ ] Implement shopping list generation for materials

### Data Management
- [ ] Create data management interface
- [ ] Implement data backup and restore
- [ ] Add data cleanup utilities
- [ ] Design database optimization tools

## Milestone 3: Advanced Features (Target: v0.4.0)

### Production Planning
- [ ] Implement multi-item production planning
- [ ] Create time-based production scheduling
- [ ] Design manufacturing facility modeling
- [ ] Implement skill level considerations
- [ ] Add blueprint invention and research planning

### Market Analysis
- [ ] Implement market trend analysis
- [ ] Create profit margin calculator
- [ ] Design arbitrage opportunity finder
- [ ] Add price alert system
- [ ] Implement order volume visualization

### Optimization
- [ ] Create material efficiency optimizer
- [ ] Implement buy vs. build decision helper
- [ ] Design resource allocation optimizer
- [ ] Add manufacturing cost reduction tools

## Milestone 4: Integration and Polish (Target: v1.0.0)

### Third-party Integration
- [ ] Implement ESI (EVE Swagger Interface) integration
- [ ] Create character skills import
- [ ] Design corporation assets integration
- [ ] Add market order placement through ESI
- [ ] Implement character wallet tracking

### User Experience
- [ ] Create guided tutorials and tooltips
- [ ] Implement keyboard shortcuts
- [ ] Design theme customization
- [ ] Add localization support
- [ ] Implement accessibility features

### Performance
- [ ] Optimize database queries
- [ ] Implement data caching
- [ ] Reduce memory usage for large datasets
- [ ] Add multi-threading for intensive operations
- [ ] Design background processing for long operations

### Deployment
- [ ] Create installer packages
- [ ] Implement auto-update mechanism
- [ ] Design crash reporting system
- [ ] Add telemetry for usage statistics (opt-in)
- [ ] Create comprehensive user manual

## Future Considerations

- Mobile companion app
- Web interface for remote access
- Corporation-level manufacturing planning
- Integration with other EVE tools and services
- Cloud sync for user preferences and plans 