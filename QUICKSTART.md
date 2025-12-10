# Quick Deployment Reference

## Initial Setup (One-time)

### 1. Create Digital Ocean Droplet
```bash
# Create droplet at: https://cloud.digitalocean.com/droplets/new
# Choose: Ubuntu 22.04, Basic $6/month, SSH keys
# Note the IP address
```

### 2. Setup Droplet
```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Download and run setup script
curl -o setup-droplet.sh https://raw.githubusercontent.com/swe-students-fall2025/5-final-superfunteam/main/setup-droplet.sh
chmod +x setup-droplet.sh
./setup-droplet.sh
```

### 3. Configure GitHub Secrets
Go to: `https://github.com/swe-students-fall2025/5-final-superfunteam/settings/secrets/actions`

Add these secrets:
- **DOCKER_USERNAME**: Your Docker Hub username
- **DOCKER_PASSWORD**: Your Docker Hub password/token
- **DROPLET_IP**: Your droplet's IP address
- **DROPLET_USER**: SSH user (usually `root`)
- **DROPLET_SSH_KEY**: Your private SSH key

### 4. Update docker-compose.prod.yml
Replace `${DOCKER_USERNAME}` with your actual Docker Hub username in `.env` file on the droplet.

## Automated Deployment

Every push to `main` branch automatically:
1. Builds Docker image
2. Pushes to Docker Hub
3. Deploys to droplet

## Manual Deployment

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Run deploy script
cd /opt/nyu-study-spaces
./deploy.sh
```

## Common Commands

### Check Status
```bash
cd /opt/nyu-study-spaces
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f webapp
```

### Restart App
```bash
cd /opt/nyu-study-spaces
docker-compose -f docker-compose.prod.yml restart
```

### Stop App
```bash
cd /opt/nyu-study-spaces
docker-compose -f docker-compose.prod.yml down
```

### Start App
```bash
cd /opt/nyu-study-spaces
docker-compose -f docker-compose.prod.yml up -d
```

### View Logs
```bash
cd /opt/nyu-study-spaces
docker-compose -f docker-compose.prod.yml logs -f
```

### Clean Up
```bash
docker system prune -a -f
```

## Access Your Application

- **HTTP:** http://YOUR_DROPLET_IP
- **Direct:** http://YOUR_DROPLET_IP:5001

## Troubleshooting

### GitHub Action Fails
- Check all secrets are set correctly
- Verify SSH key has no passphrase
- Check droplet is accessible

### App Not Starting
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs webapp

# Check if MongoDB is healthy
docker-compose -f docker-compose.prod.yml ps mongodb
```

### Can't Access Application
```bash
# Check nginx
sudo systemctl status nginx

# Check firewall
sudo ufw status

# Test locally on droplet
curl http://localhost:5001
```
