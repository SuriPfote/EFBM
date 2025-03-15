# EVE Frontier Blueprint Miracle - Data Structure

## Overview

This document describes the data structures used in the EVE Frontier Blueprint Miracle application, focusing on the JSON files and their relationships.

## JSON Data Files

The application uses several JSON files from the EVE Frontier game data:

### types_filtered.json

Contains information about item types in the game.

```json
{
  "79009": {
    "basePrice": 50000.0,
    "capacity": 0.0,
    "descriptionID": 680959,
    "groupID": 257,
    "iconID": 33,
    "isDynamicType": 0,
    "mass": 0.0,
    "platforms": 0,
    "portionSize": 1,
    "published": 1,
    "raceID": 8,
    "radius": 1.0,
    "typeID": 79009,
    "typeNameID": "Stellar Reconnaissance",
    "volume": 0.01
  }
}
```

**Key Fields:**

- `typeID`: Numeric identifier for the item type
- `typeNameID`: Actual name string (not an ID reference)
- `groupID`: Reference to the group this type belongs to
- `published`: Boolean flag (1 = published, 0 = unpublished)
- `basePrice`: Base price of the item

**Special Notes:**

- In this format, `typeNameID` contains the actual name string, not an ID reference

### groups.json

Contains information about item groups.

```json
{
  "4780": {
    "anchorable": 0,
    "anchored": 0,
    "categoryID": 4,
    "fittableNonSingleton": 0,
    "groupID": 4780,
    "groupNameID": "Manufacturing Component",
    "published": 1,
    "useBasePrice": 1
  }
}
```

**Key Fields:**

- `groupID`: Numeric identifier for the group
- `groupNameID`: Actual name string (not an ID reference)
- `categoryID`: Reference to the category this group belongs to
- `published`: Boolean flag (1 = published, 0 = unpublished)

### categories.json

Contains information about item categories.

```json
{
  "4": {
    "categoryID": 4,
    "categoryNameID": "Material",
    "published": 1
  }
}
```

**Key Fields:**

- `categoryID`: Numeric identifier for the category
- `categoryNameID`: Actual name string (not an ID reference)
- `published`: Boolean flag (1 = published, 0 = unpublished)

### blueprints.json

Contains information about manufacturing blueprints.

```json
{
  "blueprints": {
    "1234": {
      "activities": {
        "manufacturing": {
          "materials": [
            {
              "typeID": 34,
              "quantity": 100
            },
            {
              "typeID": 35,
              "quantity": 50
            }
          ],
          "products": [
            {
              "typeID": 500,
              "quantity": 1
            }
          ],
          "time": 600
        }
      },
      "blueprintTypeID": 1234,
      "maxProductionLimit": 10
    }
  }
}
```

**Key Fields:**

- `blueprintTypeID`: Numeric identifier for the blueprint
- `activities.manufacturing.materials`: Array of materials needed to craft the item
- `activities.manufacturing.products`: Array of products produced by the blueprint
- `activities.manufacturing.time`: Time required for manufacturing

**Special Structure:**

- Data is inside a nested `blueprints` object, which the EveDataMapper extracts

### unified_market_data.json

Contains market price data for items at different stations.

```json
{
  "market_data": {
    "34": {
      "10000002": {
        "sell": 1000.0,
        "buy": 900.0,
        "updated": "2023-01-01T12:00:00Z"
      }
    }
  },
  "stations": {
    "10000002": {
      "name": "Jita",
      "region": "The Forge"
    }
  },
  "last_updated": "2023-01-01T12:00:00Z"
}
```

**Key Fields:**

- `market_data`: Object mapping item IDs to station IDs to price data
- `stations`: Object mapping station IDs to station information
- `last_updated`: Timestamp of when the market data was last updated

## Data Relationships

The following relationships exist between the data files:

1. **Types to Groups**: Each item type belongs to a group via the `groupID` field
2. **Groups to Categories**: Each group belongs to a category via the `categoryID` field
3. **Products to Blueprints**: Each product is produced by a blueprint via the `activities.manufacturing.products` array
4. **Materials to Types**: Each material in a blueprint references a type via the `typeID` field

## Data Mapping

The `EveDataMapper` class is responsible for loading and mapping relationships between these data files. It creates the following mappings:

- `type_to_group`: Maps type IDs to group IDs
- `group_to_category`: Maps group IDs to category IDs
- `type_to_blueprint`: Maps product type IDs to blueprint IDs
- `type_to_market_group`: Maps type IDs to market group IDs

## Special Considerations

1. **Type Name Handling**: The `typeNameID` field in `types_filtered.json` contains the actual name string, not an ID reference
2. **Blueprint Structure**: The `blueprints.json` file has a nested structure with a `blueprints` object
3. **ID Consistency**: All IDs should be handled as strings for consistency, even though they are numeric in the JSON files
4. **Published Flag**: Only published items (with `published: 1`) should be used in the application
