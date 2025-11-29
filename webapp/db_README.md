# MongoDB Database Documentation

## Overview

The NYU Printer Status Reporter uses MongoDB to store printer information and user-submitted status reports. The database uses a two-collection design that separates static printer information from dynamic status reports.

## Collections

### 1. `printers` Collection

Stores permanent information about printer locations across NYU campus.

#### Schema Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Auto | MongoDB's unique identifier |
| `name` | String | Yes | Printer name (e.g., "Bobst Library Printer") |
| `location` | String | Yes | Full location description |
| `building` | String | Yes | Building name |
| `floor` | String | Yes | Floor number or letter |
| `created_at` | DateTime | Yes | When printer was added to system |
| `updated_at` | DateTime | Yes | Last update timestamp |

#### Example Document

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "Bobst Library - Main Floor Printer",
  "location": "Elmer Holmes Bobst Library - 1st Floor",
  "building": "Bobst Library",
  "floor": "1",
  "created_at": ISODate("2025-11-28T10:00:00Z"),
  "updated_at": ISODate("2025-11-28T10:00:00Z")
}
```

#### Indexes

- `name_1` - For searching printers by name
- `location_1` - For location-based queries
- `building_1` - For filtering by building
- `created_at_-1` - For sorting by creation date

### 2. `reports` Collection

Stores user-submitted status reports for printers. This is a time-series collection where each document represents a single status report at a point in time.

#### Schema Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Auto | MongoDB's unique identifier |
| `printer_id` | String | Yes | Reference to printer `_id` |
| `status` | String | Yes | Current status (see status values below) |
| `paper_level` | Integer | Yes | Paper level 0-100% |
| `toner_level` | Integer | Yes | Toner level 0-100% |
| `reported_by` | String | No | Username or "Anonymous" |
| `comments` | String | No | Optional user comments |
| `timestamp` | DateTime | Yes | When report was submitted |

#### Status Values

- `available` - Printer is working and available
- `busy` - Printer is currently in use
- `offline` - Printer is not responding or turned off
- `out_of_paper` - Printer has no paper
- `out_of_toner` - Printer has no toner

#### Example Document

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "printer_id": "507f1f77bcf86cd799439011",
  "status": "available",
  "paper_level": 85,
  "toner_level": 70,
  "reported_by": "john_doe",
  "comments": "Just refilled the paper tray",
  "timestamp": ISODate("2025-11-28T14:30:00Z")
}
```

#### Indexes

- `printer_id_1_timestamp_-1` - **Compound index** (most important)
  - Efficiently retrieves recent reports for a specific printer
  - Used in: GET /api/printers/<id>, main page display
- `timestamp_-1` - For chronological sorting of all reports
- `status_1` - For filtering reports by status

## Query Patterns

### Get Most Recent Status for a Printer

```javascript
db.reports.find({ printer_id: "507f1f77bcf86cd799439011" })
  .sort({ timestamp: -1 })
  .limit(1)
```

### Get All Recent Reports (Last 50)

```javascript
db.reports.find()
  .sort({ timestamp: -1 })
  .limit(50)
```

### Find Available Printers

```javascript
// Get latest report for each printer, then filter
// This requires aggregation pipeline
db.reports.aggregate([
  { $sort: { timestamp: -1 } },
  { $group: {
      _id: "$printer_id",
      latest: { $first: "$$ROOT" }
  }},
  { $match: { "latest.status": "available" } }
])
```

### Get Report History for a Printer

```javascript
db.reports.find({ printer_id: "507f1f77bcf86cd799439011" })
  .sort({ timestamp: -1 })
  .limit(10)
```

## Design Rationale

### Why Two Collections?

1. **Separation of Concerns**: Static printer info vs. dynamic status reports
2. **History Tracking**: Keep all historical status reports
3. **Scalability**: Reports collection can grow independently
4. **Query Efficiency**: Indexed queries for most recent status

### Why Store Reports Instead of Just Current Status?

1. **Audit Trail**: See who reported what and when
2. **Trend Analysis**: Track printer reliability over time
3. **Community Trust**: Multiple reports validate accuracy
4. **Debugging**: Investigate reported issues

### Index Strategy

The compound index `(printer_id, timestamp)` is critical for performance:
- MongoDB can use it to find all reports for a printer
- The timestamp ordering ensures the most recent is first
- No additional sort operation needed in application code

## Setup Instructions

### 1. Initialize Schema

Run the schema initialization script:

```bash
cd webapp
export MONGO_URI=mongodb://localhost:27017/nyu_printers
python db_schema.py
```

Expected output:
```
✓ Created 'printers' collection
✓ Created index on printers.name
✓ Created index on printers.location
✓ Created index on printers.building
✓ Created index on printers.created_at
✓ Created 'reports' collection
✓ Created compound index on reports.printer_id + timestamp
✓ Created index on reports.timestamp
✓ Created index on reports.status

✅ Database schema setup complete!
```

### 2. Seed Sample Data

Populate with NYU printer locations:

```bash
cd webapp
python seed_data.py
```

This adds 10 sample printer locations and 3 status reports.

### 3. Verify Setup

Connect to MongoDB and verify:

```bash
mongosh mongodb://localhost:27017/nyu_printers

# List collections
show collections

# Check printers
db.printers.countDocuments()
db.printers.findOne()

# Check reports
db.reports.countDocuments()
db.reports.findOne()

# Verify indexes
db.printers.getIndexes()
db.reports.getIndexes()
```

## Maintenance

### Clear All Data

```javascript
db.printers.deleteMany({})
db.reports.deleteMany({})
```

### Backup Database

```bash
mongodump --uri="mongodb://localhost:27017/nyu_printers" --out=/backup/path
```

### Restore Database

```bash
mongorestore --uri="mongodb://localhost:27017/nyu_printers" /backup/path/nyu_printers
```

## Performance Considerations

- **Reports Growth**: The reports collection will grow over time. Consider:
  - Archiving old reports (older than 30 days)
  - Setting up TTL index for automatic cleanup
  - Implementing pagination for report queries

- **Index Maintenance**: MongoDB automatically maintains indexes, but monitor:
  - Index size vs. collection size
  - Query performance with explain()
  
- **Connection Pooling**: Use PyMongo's connection pooling in production

## Security

- **Never commit credentials**: Use environment variables
- **Access Control**: Set up MongoDB users with appropriate permissions
- **Network Security**: Use MongoDB Atlas or firewall rules
- **Input Validation**: Validate all data before insertion (done in Flask app)
