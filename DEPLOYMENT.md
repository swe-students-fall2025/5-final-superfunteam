# Digital Ocean Droplet Deployment Guide

This guide will help you deploy the NYU Study Spaces application to a Digital Ocean droplet with automated GitHub Actions deployment.

## Prerequisites

- A Digital Ocean account
- Docker Hub account
- GitHub repository access

## Step 1: Create a Digital Ocean Droplet

1. **Create a new droplet:**
   - Go to https://cloud.digitalocean.com/droplets/new
   - Choose **Ubuntu 22.04 LTS** as the OS
   - Select a plan (Basic $6/month is sufficient to start)
   - Choose a datacenter region close to your users
   - **Authentication:** Select SSH keys (or Password)
   - Give it a hostname: `nyu-study-spaces`

2. **Note the droplet's IP address** after creation

## Step 2: Set Up the Droplet

SSH into your droplet and run the setup script:

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Download the setup script
curl -o setup-droplet.sh https://raw.githubusercontent.com/swe-students-fall2025/5-final-superfunteam/main/setup-droplet.sh

# Make it executable
chmod +x setup-droplet.sh

# Run the setup script
./setup-droplet.sh
```

This script will:
- Install Docker and Docker Compose
- Install nginx as a reverse proxy
- Clone your repository to `/opt/nyu-study-spaces`
- Create a secure `.env` file
- Configure the firewall
- Start the application

## Step 3: Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets:

1. **DOCKER_USERNAME**
   - Your Docker Hub username

2. **DOCKER_PASSWORD**
   - Your Docker Hub password or access token
   - Generate at: https://hub.docker.com/settings/security

3. **DROPLET_IP**
   - Your Digital Ocean droplet's IP address
   - Example: `165.227.123.45`

4. **DROPLET_USER**
   - SSH username for the droplet
   - Usually `root` or your created user

5. **DROPLET_SSH_KEY**
   - Your private SSH key for accessing the droplet
   - To get it: `cat ~/.ssh/id_rsa` (on your local machine)
   - Or generate a new one:
     ```bash
     ssh-keygen -t rsa -b 4096 -f ~/.ssh/droplet_deploy_key
     ```
   - Add the public key to droplet's `~/.ssh/authorized_keys`
   - Copy the private key content to this secret

## Step 4: Test Manual Deployment

Before relying on automated deployment, test manually:

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Navigate to app directory
cd /opt/nyu-study-spaces

# Run deploy script
./deploy.sh
```

## Step 5: Configure Docker Hub Image

Update `docker-compose.yml` to use your Docker Hub username:

```yaml
webapp:
  build: ./webapp
  image: YOUR_DOCKER_USERNAME/nyu-study-spaces-webapp:latest
  # ... rest of config
```

Replace `YOUR_DOCKER_USERNAME` with your actual Docker Hub username.

## Step 6: Push to GitHub

Once everything is configured:

```bash
git add .
git commit -m "Configure automated droplet deployment"
git push origin main
```

The GitHub Action will:
1. Build the Docker image
2. Push to Docker Hub
3. SSH into your droplet
4. Pull the latest code
5. Pull the latest Docker images
6. Restart the application

## Accessing Your Application

- **Via nginx (port 80):** http://YOUR_DROPLET_IP
- **Direct access (port 5001):** http://YOUR_DROPLET_IP:5001

## Monitoring and Management

### Check Application Status
```bash
ssh root@YOUR_DROPLET_IP
cd /opt/nyu-study-spaces
docker-compose ps
docker-compose logs -f webapp
```

### View nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Application
```bash
cd /opt/nyu-study-spaces
docker-compose restart
```

### Update Environment Variables
```bash
cd /opt/nyu-study-spaces
nano .env
docker-compose restart
```

## Adding a Domain Name (Optional)

1. **Point your domain to the droplet:**
   - Add an A record pointing to your droplet IP

2. **Update nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/nyu-study-spaces
   ```
   
   Change `server_name _;` to `server_name yourdomain.com;`

3. **Install SSL certificate (recommended):**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

4. **Restart nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

## Troubleshooting

### Deployment fails
- Check GitHub Actions logs
- Verify all secrets are correctly set
- Ensure SSH key has proper permissions

### Application not accessible
```bash
# Check if containers are running
docker-compose ps

# Check container logs
docker-compose logs webapp

# Check nginx status
sudo systemctl status nginx

# Check firewall
sudo ufw status
```

### Out of disk space
```bash
# Clean up Docker
docker system prune -a -f --volumes

# Check disk usage
df -h
```

## Security Best Practices

1. **Change default SSH port** (optional but recommended)
2. **Disable root login** and use a regular user with sudo
3. **Keep system updated:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```
4. **Set up automated backups** for MongoDB data
5. **Use strong passwords** and SSH keys only
6. **Enable automatic security updates:**
   ```bash
   sudo apt-get install unattended-upgrades
   sudo dpkg-reconfigure --priority=low unattended-upgrades
   ```

## Next Steps

- Set up monitoring (e.g., Uptime Robot, Datadog)
- Configure automated database backups
- Set up SSL/TLS certificates
- Implement log aggregation
- Add health check endpoints
