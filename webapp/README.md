# NYU Printer Status Web App

Flask-PyMongo web application for monitoring NYU printer status across campus.

## Database Schema

### Collections

#### 1. `printers` Collection
Stores information about printer locations across NYU campus.

**Schema:**
```json
{
  "_id": ObjectId,
  "name": String,              // e.g., "Bobst Library Printer"
  "location": String,          // e.g., "Bobst Library - 2nd Floor"
  "building": String,          // e.g., "Bobst Library"
  "floor": String,             // e.g., "2"
  "created_at": DateTime,      // When printer was added
  "updated_at": DateTime       // Last update to printer info
}
```

**Indexes:**
- `name` (ascending)
- `location` (ascending)
- `building` (ascending)
- `created_at` (descending)

#### 2. `reports` Collection
Stores user-submitted status reports for printers. The most recent report determines the printer's current status.

**Schema:**
```json
{
  "_id": ObjectId,
  "printer_id": String,        // Reference to printer _id
  "status": String,            // "available", "busy", "offline", "out_of_paper", "out_of_toner"
  "paper_level": Integer,      // 0-100 percentage
  "toner_level": Integer,      // 0-100 percentage
  "reported_by": String,       // Username or "Anonymous"
  "comments": String,          // Optional user comments
  "timestamp": DateTime        // When report was submitted
}
```

**Indexes:**
- Compound index: `printer_id` (ascending) + `timestamp` (descending) - For efficient retrieval of recent reports
- `timestamp` (descending) - For sorting all reports by time
- `status` (ascending) - For filtering by status

**Design Notes:**
- Printer status is **not** stored in the `printers` collection
- Status is determined by querying the most recent report from `reports` collection
- This design allows tracking status history and changes over time
- Reports are sorted by timestamp descending, so the first report is the most recent

### Database Setup

#### Initialize Schema and Indexes

```bash
cd webapp
python db_schema.py
```

This will:
- Create the `printers` and `reports` collections
- Set up all necessary indexes for optimal query performance
- Display confirmation of created collections and indexes

#### Seed Sample Data

```bash
cd webapp
python seed_data.py
```

This will:
- Insert 10 sample NYU printer locations across campus
- Add 3 sample status reports for demonstration
- Prompt before overwriting existing data

**Sample Locations Include:**
- Bobst Library (multiple floors)
- Kimmel Center
- Courant Institute
- Tandon School of Engineering
- Stern School of Business
- Silver Center
- And more...

For detailed database documentation, see [db_README.md](./db_README.md).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your MongoDB URI and secret key
```

3. Run the application:
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## API Endpoints

### Printers
- `GET /api/printers` - Get all printers
- `GET /api/printers/<id>` - Get specific printer with recent reports
- `POST /api/printers` - Add new printer
- `PUT /api/printers/<id>` - Update printer info (name, location, etc.)
- `DELETE /api/printers/<id>` - Delete printer

### Reports (User-submitted status updates)
- `POST /api/reports` - Submit a printer status report
- `GET /api/reports` - Get all reports (most recent first)
- `GET /api/reports?printer_id=<id>` - Get reports for specific printer

### Health
- `GET /health` - Health check

**Note:** Printer status is determined by the most recent user report, not stored directly on the printer.

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
webapp/
├── app.py              # Main Flask application
├── db_schema.py        # MongoDB schema and index setup
├── seed_data.py        # Sample data population script
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── README.md          # This file
├── db_README.md       # Detailed database documentation
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   └── index.html    # Home page
├── static/           # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── tests/            # Test files
    └── test_app.py
```
