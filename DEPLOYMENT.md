# Deployment Guide

This guide covers deployment setup for the NYU Printer Status Reporter application.

## Table of Contents
1. [Docker Hub Setup](#docker-hub-setup)
2. [GitHub Secrets Configuration](#github-secrets-configuration)
3. [Local Docker Testing](#local-docker-testing)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Digital Ocean Deployment](#digital-ocean-deployment)

---

## Docker Hub Setup

### Step 1: Create Docker Hub Account

1. Go to [Docker Hub](https://hub.docker.com/)
2. Click "Sign Up" and create a free account
3. Verify your email address
4. Log in to your account

### Step 2: Create Repository

1. Click "Create Repository" button
2. Configure repository:
   - **Name**: `nyu-printer-webapp`
   - **Visibility**: Public (free) or Private (requires paid account)
   - **Description**: "NYU Printer Status Reporter - Flask/PyMongo Web Application"
3. Click "Create"

### Step 3: Note Your Credentials

You'll need these for GitHub secrets:
- **Username**: Your Docker Hub username (e.g., `johndoe`)
- **Password**: Your Docker Hub password OR an access token (recommended)

**To create an access token (more secure):**
1. Go to Account Settings → Security
2. Click "New Access Token"
3. Name it "GitHub Actions"
4. Set permissions to "Read, Write, Delete"
5. Copy the token (you won't see it again!)

---

## GitHub Secrets Configuration

### Step 1: Access Repository Secrets

1. Go to your GitHub repository: `https://github.com/swe-students-fall2025/5-final-superfunteam`
2. Click "Settings" tab
3. In left sidebar, click "Secrets and variables" → "Actions"

### Step 2: Add Docker Hub Secrets

Click "New repository secret" and add:

**Secret 1: DOCKER_USERNAME**
- Name: `DOCKER_USERNAME`
- Value: Your Docker Hub username (e.g., `johndoe`)

**Secret 2: DOCKER_PASSWORD**
- Name: `DOCKER_PASSWORD`
- Value: Your Docker Hub password or access token

### Step 3: Add Digital Ocean Secret (for deployment)

**Secret 3: DIGITALOCEAN_ACCESS_TOKEN**
- Name: `DIGITALOCEAN_ACCESS_TOKEN`
- Value: Your Digital Ocean API token

**To get Digital Ocean token:**
1. Log in to [Digital Ocean](https://cloud.digitalocean.com/)
2. Click "API" in left sidebar
3. Click "Generate New Token"
4. Name it "GitHub Actions Deploy"
5. Check "Write" permission
6. Copy the token

### Step 4: Verify Secrets

After adding secrets, you should see:
- ✅ `DOCKER_USERNAME`
- ✅ `DOCKER_PASSWORD`
- ✅ `DIGITALOCEAN_ACCESS_TOKEN`

**Important:** Secrets are hidden after creation. You cannot view them again, only update them.

---

## Local Docker Testing

### Prerequisites

- Docker installed and running
- Docker Compose installed

### Step 1: Test Individual Dockerfile Build

```bash
# Navigate to webapp directory
cd webapp

# Build the Docker image
docker build -t nyu-printer-webapp:test .

# Verify the build
docker images | grep nyu-printer-webapp
```

### Step 2: Test with Docker Compose

```bash
# Navigate to project root
cd ..

# Build and start all services
docker-compose up --build

# Expected output:
# - mongodb container starts
# - webapp container starts
# - Health check passes
# - Server listening on port 5000
```

### Step 3: Test the Application

**Open browser:** http://localhost:5000

**Test API endpoints:**
```bash
# Health check
curl http://localhost:5000/health

# Get printers
curl http://localhost:5000/api/printers

# Get reports
curl http://localhost:5000/api/reports
```

### Step 4: Initialize Database (First Time Only)

```bash
# Run database setup
docker-compose run --rm setup

# Expected output:
# ✅ Created printers collection with indexes
# ✅ Created reports collection with indexes
# ✅ Successfully inserted 10 sample printers!
```

### Step 5: Stop and Clean Up

```bash
# Stop containers
docker-compose down

# Remove volumes (if you want to reset database)
docker-compose down -v

# Remove images (to test clean build)
docker rmi nyu-printer-webapp:test
```

### Common Issues

**Port already in use:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

**MongoDB connection refused:**
- Wait 10-15 seconds for MongoDB to fully start
- Check health: `docker-compose ps`
- View logs: `docker-compose logs mongodb`

**Permission denied:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

---

## CI/CD Pipeline

### CI Workflow (`.github/workflows/webapp-ci.yml`)

Automatically runs on:
- Push to `main` or `setup` branches
- Pull requests to `main`
- Changes to `webapp/` directory

**Stages:**

1. **MongoDB Integration** - Tests database subsystem
   - Validates `db_schema.py` creates collections and indexes
   - Verifies correct number of indexes (5 on printers, 4 on reports)
   - Tests `seed_data.py` inserts sample data
   - Confirms at least 10 printers and 3 reports

2. **Test** - Tests webapp with real MongoDB
   - Sets up Python 3.11 and MongoDB 7.0 service
   - Initializes test database
   - Runs pytest with coverage
   - Fails if coverage < 80%

3. **Build**
   - Builds Docker image
   - Tests image can run
   - Uses cache for faster builds

4. **Docker Push** (only on `main` branch)
   - Logs into Docker Hub
   - Pushes image with tags:
     - `latest`
     - Git commit SHA

### CD Workflow (`.github/workflows/webapp-deploy.yml`)

Automatically deploys on:
- Push to `main` branch
- Changes to `webapp/` or `docker-compose.yml`
- Can also be triggered manually from GitHub Actions UI

**Stages:**

1. **Build and Push**
   - Builds Docker image
   - Pushes to Docker Hub with commit SHA tag

2. **Deploy to Digital Ocean**
   - Updates Digital Ocean App Platform
   - Deploys new container image
   - Uses commit SHA for version tracking

3. **Notifications**
   - Reports deployment success/failure
   - Shows deployed image tags

### Viewing CI Results

1. Go to "Actions" tab on GitHub
2. Click on a workflow run
3. View test results, coverage, and build logs

### Triggering CI Manually

```bash
# Push changes to trigger CI
git add .
git commit -m "feat: add new feature"
git push origin setup

# Or trigger from GitHub UI
# Go to Actions → Web App CI → Run workflow
```

---

## Digital Ocean Deployment

### Option 1: Digital Ocean App Platform (Recommended)

**Step 1: Create App**
1. Log in to Digital Ocean
2. Click "Create" → "Apps"
3. Connect your GitHub repository
4. Select `5-final-superfunteam` repository
5. Select `main` branch

**Step 2: Configure App**
1. **Web Service:**
   - Name: `webapp`
   - Source Directory: `/webapp`
   - Dockerfile path: `/webapp/Dockerfile`
   - HTTP Port: 5000
   - Instance Size: Basic ($5/month)

2. **Database:**
   - Add MongoDB database ($15/month)
   - Or use MongoDB Atlas (free tier available)

**Step 3: Environment Variables**
Add these in App Settings → Environment Variables:
```
MONGO_URI=mongodb://username:password@host:27017/nyu_printers
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

**Step 4: Deploy**
- Click "Deploy"
- Wait 5-10 minutes
- Get your live URL: `https://nyu-printer-webapp-xxxxx.ondigitalocean.app`

### Option 2: Digital Ocean Droplet (Manual)

**Step 1: Create Droplet**
```bash
# Specs:
# - Ubuntu 22.04 LTS
# - Basic plan: $6/month (1GB RAM)
# - Enable backups (optional)
```

**Step 2: SSH into Droplet**
```bash
ssh root@your-droplet-ip
```

**Step 3: Install Docker**
```bash
# Update packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

**Step 4: Clone Repository**
```bash
git clone https://github.com/swe-students-fall2025/5-final-superfunteam.git
cd 5-final-superfunteam
```

**Step 5: Configure Environment**
```bash
cp .env.example .env
nano .env

# Set production values:
# MONGO_URI=mongodb://mongodb:27017/nyu_printers
# SECRET_KEY=generate-a-secure-random-key
# FLASK_ENV=production
```

**Step 6: Deploy**
```bash
# Start services
docker-compose up -d

# Initialize database
docker-compose run --rm setup

# Check status
docker-compose ps
docker-compose logs webapp
```

**Step 7: Set Up Nginx (Optional)**
```bash
# Install Nginx
apt install nginx -y

# Configure reverse proxy
nano /etc/nginx/sites-available/nyu-printers

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
ln -s /etc/nginx/sites-available/nyu-printers /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Option 3: MongoDB Atlas (Free Database)

**Step 1: Create Cluster**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for free account
3. Create free M0 cluster
4. Select region closest to your app

**Step 2: Configure Access**
1. Create database user with password
2. Add IP address to whitelist:
   - For testing: `0.0.0.0/0` (anywhere)
   - For production: Your droplet/app IP

**Step 3: Get Connection String**
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/nyu_printers?retryWrites=true&w=majority
```

**Step 4: Update Environment Variable**
```bash
MONGO_URI=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/nyu_printers?retryWrites=true&w=majority
```

---

## Deployment Checklist

### Before Deployment

- [ ] All tests pass locally
- [ ] Docker builds successfully
- [ ] `docker-compose up` works locally
- [ ] Database schema is initialized
- [ ] Environment variables configured
- [ ] Docker Hub credentials added to GitHub secrets
- [ ] CI pipeline is green

### After Deployment

- [ ] Application is accessible via URL
- [ ] Database connection works
- [ ] API endpoints respond correctly
- [ ] Can submit status reports
- [ ] Can view printer list
- [ ] Health check returns OK
- [ ] No errors in application logs
- [ ] SSL/HTTPS configured (if using custom domain)

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check application health
curl https://your-app-url/health

# Expected response:
{"status": "healthy", "database": "connected"}
```

### View Logs

**Docker Compose:**
```bash
docker-compose logs -f webapp
docker-compose logs -f mongodb
```

**Digital Ocean App Platform:**
- Go to App → Runtime Logs

### Database Backup

**MongoDB Atlas:**
- Automatic backups included in free tier

**Manual Backup:**
```bash
# Export database
docker exec mongodb mongodump --out=/backup/nyu-printers-$(date +%Y%m%d)

# Download backup
docker cp mongodb:/backup ./backups
```

### Updating Application

**Automatic (CI/CD):**
1. Push to `main` branch
2. CI builds and pushes Docker image
3. Digital Ocean auto-deploys new version

**Manual:**
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs webapp

# Common issues:
# - MongoDB not ready: wait 30 seconds
# - Port conflict: change port in docker-compose.yml
# - Environment variables missing: check .env file
```

### Database Connection Errors

```bash
# Test MongoDB connection
docker exec -it mongodb mongosh

# Check connection string format
echo $MONGO_URI

# Verify network
docker network ls
docker network inspect printer-network
```

### CI/CD Pipeline Fails

1. Check "Actions" tab for error details
2. Common issues:
   - Test failures: fix failing tests
   - Coverage too low: add more tests
   - Docker Hub login: verify secrets
   - Build errors: test locally first

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Digital Ocean Tutorials](https://www.digitalocean.com/community/tutorials)
- [MongoDB Atlas Docs](https://docs.atlas.mongodb.com/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Flask Deployment](https://flask.palletsprojects.com/en/3.0.x/deploying/)

---

## Support

For issues or questions:
1. Check this deployment guide
2. Review application logs
3. Check GitHub Issues
4. Contact team members:
   - Evelynn (Deployment Engineer)
   - Connor Lee (MongoDB)
   - Zeba Shafi (Backend)
