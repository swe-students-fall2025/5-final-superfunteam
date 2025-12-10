[![Build Status](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-ci.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-ci.yml)
[![Deploy Status](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-deploy.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-deploy.yml)

# NYU Study Spaces Status Reporter

A real-time, community-driven monitoring system that reports on the status and quality of study spaces at various NYU locations. Students can submit reviews with ratings for silence, crowdedness, and overall quality, helping others find the best study spaces before making trips across campus.

## Team Members

- [Zeba Shafi](https://github.com/Zeba-Shafi)
- [Jubilee Tang](https://github.com/MajesticSeagull26)
- [Connor Lee](https://github.com/Connorlee487)
- [Catherine Yu](https://github.com/catherineyu2014)
- [Evelynn Mak](https://github.com/evemak)

## Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose installed
- Git for cloning the repository
- A Docker Hub account (for pushing custom images)

## Configuration

### 1. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=production
```

**Important**: Never commit the actual `.env` file to version control!

### 2. MongoDB Setup

No additional configuration needed. MongoDB will automatically:
- Create the database (default: `proj4`) on first run
- Store data in a Docker volume for persistence

## Running the Application

### Using Docker Compose (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/swe-students-fall2025/5-final-superfunteam.git
cd 5-final-superfunteam
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your SECRET_KEY
```

3. **Build and start all containers**:
```bash
docker-compose up --build
```

4. **Access the application**:
   - Web App: http://localhost:5001
   - MongoDB: localhost:27017

5. **Stop the application**:
```bash
# Stop containers (keeps data)
docker-compose down

# Stop containers and remove volumes (clean slate)
docker-compose down -v
```

### Running Locally (Development)

1. **Install dependencies**:
```bash
cd webapp
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export MONGO_URI=mongodb://localhost:27017/proj4
export SECRET_KEY=dev-secret-key
export FLASK_ENV=development
```

3. **Start MongoDB** (if not using Docker):
```bash
mongod --dbpath /path/to/data/db
```

4. **Run the application**:
```bash
python app.py
```

## Seeding the Database

To populate the database with sample study spaces:

```bash
# Start the containers
docker-compose up -d

# Add sample study spaces via API
curl -X POST http://localhost:5001/api/spaces \
  -H "Content-Type: application/json" \
  -d '{
    "building": "Bobst Library",
    "sublocation": "2nd Floor Study Area"
  }'

# Add a review (requires authentication)
curl -X POST http://localhost:5001/api/reviews \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "space_id": "SPACE_ID_HERE",
    "rating": 4,
    "silence": 5,
    "crowdedness": 3,
    "review": "Great quiet space with good lighting"
  }'
```

## API Endpoints

### Study Spaces
- `GET /api/spaces` - Get all study spaces
- `GET /api/spaces/<id>` - Get specific study space with recent reviews
- `POST /api/spaces` - Add new study space
- `PUT /api/spaces/<id>` - Update study space info
- `DELETE /api/spaces/<id>` - Delete study space

### Reviews
- `POST /api/reviews` - Submit a study space review (requires authentication)
- `GET /api/reviews` - Get all reviews (most recent first)
- `GET /api/reviews?space_id=<id>` - Get reviews for specific study space

## Testing

Run the test suite:

```bash
cd webapp
pytest tests/ -v --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # On macOS
# or
start htmlcov/index.html  # On Windows
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

- **Workflow File**: `.github/workflows/webapp-ci.yml`
- **Triggers**: Push or PR to `main` branch
- **Steps**:
  1. Run unit tests with pytest
  2. Check code coverage (minimum 80%)
  3. Build Docker image
  4. Push to Docker Hub
  5. Deploy to Digital Ocean

## Technologies Used

- **Backend**: Python 3.11, Flask 3.0.0, PyMongo 4.6.0
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: MongoDB 7.0
- **Containerization**: Docker, Docker Compose
- **Web Server**: Gunicorn
- **Testing**: Pytest
- **CI/CD**: GitHub Actions
- **Deployment**: Digital Ocean

## License

This project is part of an academic exercise for NYU's Software Engineering course.
