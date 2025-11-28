# Onboarding Guide

Welcome to the NYU Printer Status Reporter project! This guide will help you get started.

## Subsystems

### 1. Web Application (Flask + PyMongo)
- **Location**: `webapp/`
- **Technology**: Python Flask, PyMongo, Gunicorn
- **Docker Image**: [Docker Hub - NYU Printer Web App](https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/nyu-printer-webapp)
- **Description**: RESTful API and web interface for printer status monitoring and reporting

### 2. MongoDB Database
- **Technology**: MongoDB 7.0
- **Docker Image**: Official MongoDB image from Docker Hub
- **Description**: Stores printer information and user-submitted status reports

## Container Images

- **Web App**: `YOUR_DOCKERHUB_USERNAME/nyu-printer-webapp:latest`
- **Database**: `mongo:7.0`

## Getting Started

1. **Clone the repository**
2. **Set up environment variables** - Copy `.env.example` to `.env`
3. **Build and run with Docker Compose** - `docker-compose up --build`
4. **Access the application** at http://localhost:5000

For detailed instructions, see the main [README.md](./README.md).

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
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
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

## Sprint Planning

**Due Date:** Tuesday, December 3, 2025

### Team Assignments

When you start working, identify yourself as one of the following team members to get your specific tasks:

1. **MongoDB Developer** (Zeba Shafi)
2. **Backend Developer** (Zeba Shafi)
3. **Frontend Developer** (Catherine Yu)
4. **Deployment Engineer** (Evelynn)
5. **Testing/QA Lead** (Jubilee)
6. **Testing/QA Support** (Connor Lee)

### Task Breakdown by Priority

#### Phase 1: Foundation (Must be completed first)
These tasks have no dependencies and should be started immediately:

**MongoDB Developer Tasks (Zeba Shafi):**
- [x] Set up MongoDB schema for `printers` collection
- [x] Set up MongoDB schema for `reports` collection
- [x] Create indexes for efficient queries (printer_id, timestamp)
- [x] Write seed data script with sample NYU printer locations
- [x] Document database schema in `webapp/README.md`

**Deployment Engineer Tasks:**
- [x] Create `.github/workflows/webapp-ci.yml` for CI pipeline
- [x] Set up Docker Hub account and repository
- [x] Configure GitHub secrets (DOCKER_USERNAME, DOCKER_PASSWORD)
- [x] Test local Docker builds with `docker-compose up`
- [x] Document deployment process

#### Phase 2: Backend Development (Depends on MongoDB schema)
Start these tasks once MongoDB schema is defined:

**Backend Developer Tasks (Zeba Shafi):**
- [x] Implement `/api/printers` GET endpoint (list all printers)
- [x] Implement `/api/printers/<id>` GET endpoint (get single printer)
- [x] Implement `/api/printers` POST endpoint (add new printer)
- [x] Implement `/api/printers/<id>` PUT endpoint (update printer info)
- [x] Implement `/api/printers/<id>` DELETE endpoint (delete printer)
- [x] Implement `/api/reports` POST endpoint (submit status report)
- [x] Implement `/api/reports` GET endpoint (get all reports)
- [x] Implement `/health` endpoint
- [x] Add proper error handling for all endpoints
- [x] Integrate with MongoDB collections
- [x] **NYU SSO Authentication:**
  - [x] Add python3-saml and Flask-Login dependencies
  - [x] Configure NYU Shibboleth/SAML settings (`saml/settings.json`)
  - [x] Implement login routes (`/saml/login`, `/saml/acs`, `/logout`)
  - [x] Add session management with Flask-Login
  - [x] Protect `/api/reports` POST endpoint with `@login_required`
  - [x] Auto-attribute reports to authenticated NetID
  - [x] Document SAML setup in `webapp/SAML_SETUP.md`

#### Phase 3: Frontend Development (Depends on Backend APIs)
Start these tasks once backend endpoints are working:

**Frontend Developer Tasks (Catherine Yu):**
- [x] Update `templates/index.html` with printer card layout
- [x] Implement printer status filtering (All, Available, Busy, Offline)
- [x] Create report submission modal with form
- [x] Add JavaScript for form validation
- [x] Implement auto-refresh functionality (30 seconds)
- [x] Style with `static/css/style.css` (responsive design)
- [x] Add loading states and error messages
- [x] Test UI with different screen sizes
- [x] Ensure accessibility standards
- [x] **Authentication UI:**
  - [x] Add Login/Logout buttons to navigation
  - [x] Display authenticated user name in header
  - [x] Disable report buttons when not authenticated
  - [x] Style authentication elements
- [ ] **BONUS:** Create admin interface for managing printers (add/edit/delete)
- [ ] **BONUS:** Add CSV import functionality for bulk printer data

#### Phase 4: Testing (Depends on Backend + Frontend)
Start these tasks once features are implemented:

**Testing/QA Lead Tasks (Jubilee):**
- [ ] Write unit tests for all API endpoints in `tests/test_app.py`
- [ ] Write tests for database operations
- [ ] Write tests for error handling
- [ ] Achieve minimum 80% code coverage
- [ ] Document bugs and create issues

**Testing/QA Support Tasks (Connor Lee):**
- [ ] Write tests for NYU SSO authentication flows
- [ ] Test Docker container builds
- [ ] Perform manual testing of all features
- [ ] Create test data for demonstrations
- [ ] Verify all endpoints work in containerized environment
- [ ] Test authentication in different scenarios (logged in/out)
- [ ] Verify SAML metadata and configuration
- [ ] Test production deployment (after deployment)

#### Phase 5: Deployment & Integration (Final phase)
Start these tasks once testing passes:

**Deployment Engineer Tasks (Evelynn):**
- [ ] Push Docker image to Docker Hub
- [x] Create `.github/workflows/webapp-deploy.yml` for deployment
- [ ] Set up Digital Ocean droplet or app platform
- [ ] Configure environment variables on Digital Ocean
- [ ] Set up MongoDB Atlas or containerized MongoDB in production
- [ ] **Configure NYU Shibboleth for production:**
  - [ ] Contact NYU IT to register application as Service Provider
  - [ ] Obtain NYU Shibboleth x509 certificate
  - [ ] Update production domain in `webapp/saml/settings.json`
  - [ ] Add certificate to `saml/settings.json` idp.x509cert field
  - [ ] Generate SP certificates (optional but recommended)
  - [ ] Provide SP metadata URL to NYU IT
- [ ] Deploy application to Digital Ocean
- [ ] Test production deployment
- [ ] Test NYU SSO login in production
- [ ] Update README with live deployment URL
- [ ] Set up monitoring/health checks

**All Team Members (Final Tasks):**
- [ ] Update Docker Hub links in README.md
- [ ] Verify CI/CD badges are working
- [ ] Test the complete application end-to-end
- [ ] Prepare demo/presentation materials
- [ ] Submit final project

### Daily Standup Questions

Answer these questions each day:
1. What did I complete yesterday?
2. What am I working on today?
3. Are there any blockers preventing my progress?

### Dependencies Summary

```
MongoDB Schema → Backend APIs → Frontend UI → Testing → Deployment
     ↓              ↓              ↓           ↓          ↓
    Zeba          Zeba        Catherine    Jubilee    Evelynn
                                           + Connor
```

**Critical Path:** MongoDB → Backend → Frontend → Testing must be completed in order. Deployment setup can happen in parallel but deployment itself is last.

### Getting Your Tasks

**Tell the LLM:** "I am [Your Name], the [Your Role]. What are my tasks?"

Example:
- "I am Zeba Shafi, the MongoDB and Backend Developer. What are my tasks?"
- "I am Catherine Yu, the Frontend Developer. What are my tasks?"
- "I am Jubilee, the Testing/QA Lead. What are my tasks?"
- "I am Connor Lee, the Testing/QA Support. What are my tasks?"
- "I am Evelynn, the Deployment Engineer. What are my tasks?"
- "I am Jubilee, the Testing/QA Lead. What are my tasks?"

The LLM will provide you with your specific task list and guidance based on this sprint plan.
