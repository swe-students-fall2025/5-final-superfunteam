[![Build Status](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-ci.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-ci.yml)
[![Deploy Status](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-deploy.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-superfunteam/actions/workflows/webapp-deploy.yml)

# NYU Printer Status Reporter

A real-time, community-driven monitoring system that reports on the operational status of printers at various NYU locations. Students and staff can submit status reports and quickly find available printers before making trips across campus.

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
- Create the `nyu_printers` database on first run
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
   - Web App: http://localhost:5000
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
export MONGO_URI=mongodb://localhost:27017/nyu_printers
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

To populate the database with sample printer locations:

```bash
# Start the containers
docker-compose up -d

# Add sample printers via API
curl -X POST http://localhost:5000/api/printers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bobst Library Printer",
    "location": "Bobst Library - 2nd Floor",
    "building": "Bobst Library",
    "floor": "2"
  }'

# Add a status report
curl -X POST http://localhost:5000/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "PRINTER_ID_HERE",
    "status": "available",
    "paper_level": 80,
    "toner_level": 60,
    "reported_by": "Student Name"
  }'
```

## API Endpoints

### Printers
- `GET /api/printers` - Get all printers
- `GET /api/printers/<id>` - Get specific printer with recent reports
- `POST /api/printers` - Add new printer
- `PUT /api/printers/<id>` - Update printer info
- `DELETE /api/printers/<id>` - Delete printer

### Reports
- `POST /api/reports` - Submit a printer status report
- `GET /api/reports` - Get all reports (most recent first)
- `GET /api/reports?printer_id=<id>` - Get reports for specific printer

### Health Check
- `GET /health` - Health check endpoint

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

## Project Structure

```
5-final-superfunteam/
├── .github/
│   └── workflows/
│       ├── webapp-ci.yml      # CI/CD pipeline
│       └── webapp-deploy.yml  # Deployment workflow
├── webapp/                     # Flask web application
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_app.py
│   ├── .dockerignore
│   ├── .env.example
│   ├── app.py
│   ├── Dockerfile
│   ├── README.md
│   └── requirements.txt
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── instructions.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## Technologies Used

- **Backend**: Python 3.11, Flask 3.0.0, PyMongo 4.6.0
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: MongoDB 7.0
- **Containerization**: Docker, Docker Compose
- **Web Server**: Gunicorn
- **Testing**: Pytest
- **CI/CD**: GitHub Actions
- **Deployment**: Digital Ocean

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

- **Onboarding Guide**: See [ONBOARDING.md](./ONBOARDING.md) for sprint planning and task breakdown
- **Database Schema**: See [webapp/README.md](./webapp/README.md) for database setup and schema documentation
- **Deployment Guide**: See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions and CI/CD setup

## License

This project is part of an academic exercise for NYU's Software Engineering course.

## Support

For issues or questions, please open an issue on GitHub or contact any team member.

