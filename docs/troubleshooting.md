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
