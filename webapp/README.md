# NYU Study Spaces Status Web App

Flask-PyMongo web application for monitoring and reviewing NYU study spaces across campus.

## Database Schema

### Collections

#### 1. `study_spaces` Collection

Stores information about study space locations across NYU campus.

**Schema:**

```json
{
  "_id": ObjectId,
  "building": String,          // e.g., "Bobst Library"
  "sublocation": String,       // e.g., "2nd Floor Study Area"
  "created_at": DateTime,      // When space was added
  "updated_at": DateTime       // Last update to space info
}
```

**Indexes:**

-   `building` (ascending)
-   `sublocation` (ascending)
-   `created_at` (descending)

#### 2. `reviews` Collection

Stores user-submitted reviews for study spaces. Reviews include ratings for overall quality, silence level, and crowdedness.

**Schema:**

```json
{
  "_id": ObjectId,
  "space_id": String,          // Reference to study_space _id
  "rating": Integer,           // 1-5 overall rating
  "silence": Integer,          // 1-5 silence level (5 = very quiet)
  "crowdedness": Integer,      // 1-5 crowdedness level (5 = very crowded)
  "review": String,            // Optional text review/comments
  "reported_by": String,       // User's NetID
  "reporter_email": String,    // User's email
  "timestamp": DateTime         // When review was submitted
}
```

**Indexes:**

-   Compound index: `space_id` (ascending) + `timestamp` (descending) - For efficient retrieval of recent reviews
-   `timestamp` (descending) - For sorting all reviews by time
-   `rating` (ascending) - For filtering by rating

**Design Notes:**

-   Study space ratings are calculated dynamically from reviews
-   Average ratings (overall, silence, crowdedness) are computed when needed
-   This design allows tracking review history and changes over time
-   Reviews are sorted by timestamp descending, so the first review is the most recent

### Database Setup

#### Initialize Schema and Indexes

```bash
cd webapp
python db_schema.py
```

This will:

-   Create the `study_spaces` and `reviews` collections
-   Set up all necessary indexes for optimal query performance
-   Display confirmation of created collections and indexes

#### Seed Sample Data

```bash
cd webapp
python seed_data.py
```

This will:

-   Insert sample NYU study space locations across campus
-   Prompt before overwriting existing data

**Sample Locations Include:**

-   Bobst Library (multiple floors)
-   Kimmel Center
-   Courant Institute
-   Tandon School of Engineering
-   Stern School of Business
-   Silver Center
-   And more...

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

### Study Spaces

-   `GET /api/spaces` - Get all study spaces
-   `GET /api/spaces/<id>` - Get specific study space with recent reviews and average ratings
-   `POST /api/spaces` - Add new study space
-   `PUT /api/spaces/<id>` - Update study space info (building, sublocation)
-   `DELETE /api/spaces/<id>` - Delete study space

### Reviews (User-submitted reviews)

-   `POST /api/reviews` - Submit a study space review (requires authentication)
-   `GET /api/reviews` - Get all reviews (most recent first)
-   `GET /api/reviews?space_id=<id>` - Get reviews for specific study space

### Authentication

-   `POST /api/register` - Register a new user with NYU email
-   `POST /api/login` - Login with email and password
-   `GET /api/user` - Get current authenticated user information (requires authentication)
-   `GET /logout` - Logout current user

### Pages

-   `GET /` - Home page showing all study spaces
-   `GET /login` - Login page
-   `GET /add-space` - Page for adding a new study space
-   `GET /map` - Page showing study spaces on Google Maps

### Health

-   `GET /health` - Health check endpoint

**Note:** Study space ratings are calculated dynamically from reviews. Average ratings (overall, silence, crowdedness) are computed when needed.

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
├── production_data.py  # Production data script (optional)
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── README.md          # This file
├── db_README.md       # Detailed database documentation
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── index.html    # Home page
│   ├── login.html    # Login/Register page
│   ├── add_space.html # Add study space page
│   └── map.html      # Map view page
├── static/           # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── tests/            # Test files
    ├── test_app.py
    ├── test_db_schema.py
    ├── test_seed_data.py
    └── test_production_data.py
```
