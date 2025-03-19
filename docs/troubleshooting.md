# EVE Frontier Blueprint Miracle - Troubleshooting Guide

## Overview

This document outlines common issues that may be encountered when using the EVE Frontier Blueprint Miracle application and provides troubleshooting steps to resolve them.

## Data Loading Issues

### Missing or Invalid JSON Files

**Symptoms:**

- Application fails to start
- Error message about missing or invalid JSON files
- Empty search results

**Troubleshooting Steps:**

1. Verify that all required JSON files are present in the `data/json` directory
2. Check file permissions to ensure the application can read the files
3. Validate JSON files for correct format using a JSON validator
4. Check the application logs for specific error messages

### Incorrect Data Paths

**Symptoms:**

- Application starts but cannot find data files
- Error messages about file not found
- Empty search results

**Troubleshooting Steps:**

1. Check the configuration settings for correct data paths
2. Verify that the directory structure matches the expected paths
3. Try using absolute paths instead of relative paths
4. Check the application logs for specific error messages

## Search Issues

### Item Names Not Found

**Symptoms:**

- Searching for known items returns no results
- "Unknown" appears in place of item names
- Error messages about missing type names

**Troubleshooting Steps:**

1. Verify that the `types_filtered.json` file contains the expected items
2. Check that the `typeNameID` field is being correctly interpreted as a name string
3. Try searching by type ID instead of name
4. Check the application logs for specific error messages

### Incorrect Search Results

**Symptoms:**

- Search returns unexpected items
- Items appear with incorrect names or details
- Search filters don't work correctly

**Troubleshooting Steps:**

1. Verify that the search term is correct
2. Check case sensitivity settings
3. Try more specific search terms
4. Check the application logs for specific error messages

## Blueprint Analysis Issues

### Missing Blueprint Information

**Symptoms:**

- Items show as not having blueprints when they should
- Blueprint details are missing or incomplete
- Error messages about missing blueprint data

**Troubleshooting Steps:**

1. Verify that the `blueprints.json` file contains the expected blueprints
2. Check that the blueprint ID mapping is correct
3. Try searching for the blueprint directly by ID
4. Check the application logs for specific error messages

### Incorrect Manufacturing Requirements

**Symptoms:**

- Blueprint shows incorrect materials or quantities
- Manufacturing costs are incorrect
- Error messages about missing or invalid material data

**Troubleshooting Steps:**

1. Verify that the blueprint data in `blueprints.json` is correct
2. Check that material type IDs are correctly mapped to items
3. Verify that quantity calculations are correct
4. Check the application logs for specific error messages

## Market Data Issues

### Missing Market Prices

**Symptoms:**

- Market prices show as 0 or "Not available"
- Error messages about missing market data
- Incorrect cost calculations

**Troubleshooting Steps:**

1. Verify that the `unified_market_data.json` file exists and is correctly formatted
2. Check that the selected station has price data for the items
3. Try selecting a different station
4. Check the application logs for specific error messages

### Incorrect Price Calculations

**Symptoms:**

- Manufacturing costs are incorrect
- Profit calculations are incorrect
- Error messages about invalid price data

**Troubleshooting Steps:**

1. Verify that the price data in `unified_market_data.json` is correct
2. Check that custom prices are being correctly applied if used
3. Verify that quantity calculations are correct
4. Check the application logs for specific error messages

## UI Issues

### UI Elements Not Displaying Correctly

**Symptoms:**

- UI elements are missing or misaligned
- Text is cut off or unreadable
- Error messages about UI components

**Troubleshooting Steps:**

1. Resize the application window
2. Check that all required UI libraries are installed
3. Verify that the display resolution meets minimum requirements
4. Check the application logs for specific error messages

### Application Crashes

**Symptoms:**

- Application closes unexpectedly
- Error messages about exceptions
- Frozen or unresponsive UI

**Troubleshooting Steps:**

1. Check the application logs for error messages
2. Verify that all required dependencies are installed
3. Check system resources (memory, disk space)
4. Try restarting the application

### Detail Panel Update Issues

**Symptoms:**
- Detail tabs not updating when selecting a new item
- Stale data displayed in detail panels
- Material lists or other details not refreshing

**Troubleshooting Steps:**
1. Ensure the selection change event is properly connected to the update method
2. Add explicit table clearing with `clearContents()` before populating new data
3. Force UI updates with `update()` and `repaint()` calls after data changes
4. Use tab index switching to force Qt to refresh content:
   ```python
   # Force the current tab to refresh
   current_index = self.details_tabs.currentIndex()
   self.details_tabs.setCurrentIndex((current_index + 1) % self.details_tabs.count())
   self.details_tabs.setCurrentIndex(current_index)
   ```

### Missing Import Errors

**Symptoms:**
- Some tabs or panels fail to update
- Error messages about undefined classes or methods
- Only some parts of the UI update when selecting items

**Troubleshooting Steps:**
1. Check import statements for missing classes
2. Ensure all required models are imported (e.g., Blueprint, BlueprintActivity, etc.)
3. Look for error messages in the application logs
4. Test each detail panel update method independently

## Profitability Analyzer Issues

### No Profitable Items Shown

**Symptoms:**
- Profitability Analyzer shows "0 profitable items found" despite having market data
- "No profit data" warnings in application logs
- Items with known profit margins not appearing in results

**Troubleshooting Steps:**
1. Check logs for division by zero errors in market statistics calculations
2. Verify that the `get_market_statistics` method is returning consistent field names
3. Ensure items that don't have manufacturing blueprints are handled correctly
4. Verify that the `calculate_production_profit` method is properly processing market data
5. Add debug logging to the `_run_analysis` method to track filter conditions

### Model Access Pattern Errors

**Symptoms:**
- AttributeError: 'SearchService' object has no attribute 'Item'
- NoneType has no attribute 'id' errors in logs
- Manufacturing details calculation fails

**Troubleshooting Steps:**
1. Ensure the Item model is properly imported in the relevant files
2. Use db.query(Item) pattern instead of relying on SearchService to access models
3. Add proper error handling for cases when blueprints are not found
4. Make sure market data is fetched correctly when manufacturing data is not available

### Inconsistent Field Names

**Symptoms:**
- KeyError on accessing market statistics fields
- Services using different field names to refer to the same data
- Market and production services not communicating correctly

**Troubleshooting Steps:**
1. Check that `get_market_statistics` returns consistent field names (e.g., 'sell_price' vs 'min_sell_price')
2. Ensure `calculate_production_profit` uses the same field names as `get_market_statistics` returns
3. Add proper null/zero checks before calculations to prevent division by zero errors
4. Update service methods to include both old and new field names for backward compatibility

## Logging and Debugging

### Enabling Debug Logging

To enable detailed debug logging:

1. Edit the configuration file to set the log level to DEBUG
2. Restart the application
3. Check the log files in the `logs` directory

### Generating Troubleshooting Reports

To generate a troubleshooting report:

1. Go to Help > Generate Troubleshooting Report
2. Save the report file
3. Include the report when seeking support

### Checking Application Logs

Application logs are stored in the `logs` directory:

- `app.log`: General application logs
- `error.log`: Error messages only
- `debug.log`: Detailed debug information (if enabled)

## Common Error Messages

### "Failed to load data file"

**Cause:** The application cannot find or read a required data file.
**Solution:** Verify that the file exists and has correct permissions.

### "Error parsing JSON data"

**Cause:** A JSON file is malformed or contains invalid data.
**Solution:** Validate the JSON file using a JSON validator.

### "Unknown type ID"

**Cause:** The application is trying to access a type ID that doesn't exist in the data.
**Solution:** Verify that the type ID exists in `types_filtered.json`.

### "Error calculating production chain"

**Cause:** The application encountered an error while calculating a production chain.
**Solution:** Check that all required blueprint and material data is available.

### "NoneType object has no attribute 'id'"

**Cause:** The application is trying to access the 'id' attribute of a None object, typically when a blueprint isn't found.
**Solution:** Add proper null checks before accessing attributes and implement error handling.

### "Division by zero" in market statistics

**Cause:** The application attempts to calculate percentages with a zero denominator.
**Solution:** Add checks to prevent division by zero when calculating spread percentages.

## Database Issues

### Database Path Resolution

**Symptoms:**
- Error messages like "no such table: blueprints" when tables are known to exist
- Database queries fail despite successful initialization
- Application works from one directory but not another

**Troubleshooting Steps:**
1. Check the database path in the configuration (`eve_frontier/config.py`)
2. Ensure the database URL uses an absolute path instead of a relative path
3. Verify that the application can locate and access the database file
4. Run the `init_database.py` script to ensure tables are created

**Solution:**
Update the database URL in `config.py` to use an absolute path:
```python
# Use an absolute path to the database file
db_url: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'eve_frontier.db'))}"
```

### Database Initialization Failure

**Symptoms:**
- Empty tables despite running the initialization script
- Error messages about missing tables
- Missing blueprint data or incomplete records

**Troubleshooting Steps:**
1. Run the `init_database.py` script with the `--force` flag to recreate all tables
2. Check the application logs for error messages
3. Verify that data files exist in the expected locations
4. Check database connections and permissions
