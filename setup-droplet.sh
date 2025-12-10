#!/bin/bash
# Setup script to run once on a new Digital Ocean droplet
# This prepares the droplet for automated deployments

set -e

echo "🔧 Setting up Digital Ocean droplet for NYU Study Spaces..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "✓ Docker already installed"
fi

# Install Docker Compose
echo "🐙 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "✓ Docker Compose already installed"
fi

# Install git
echo "📚 Installing Git..."
sudo apt-get install -y git

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/nyu-study-spaces
sudo chown -R $USER:$USER /opt/nyu-study-spaces

# Clone repository
echo "📥 Cloning repository..."
cd /opt/nyu-study-spaces
if [ ! -d ".git" ]; then
    git clone https://github.com/swe-students-fall2025/5-final-superfunteam.git .
else
    echo "✓ Repository already cloned"
    git pull origin main
fi

# Create .env file
echo "⚙️  Creating .env file..."
if [ ! -f ".env" ]; then
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    cat > .env << EOF
DOCKER_USERNAME=${DOCKER_USERNAME}
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
MONGO_URI=mongodb://mongodb:27017/proj4
EOF
    echo "✓ .env file created with random SECRET_KEY"
else
    echo "✓ .env file already exists"
fi

# Make deploy script executable
chmod +x deploy.sh

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 5001/tcp
sudo ufw --force enable

# Install nginx (optional - for reverse proxy)
echo "🌐 Installing nginx..."
sudo apt-get install -y nginx

# Create nginx configuration
echo "⚙️  Configuring nginx as reverse proxy..."
sudo tee /etc/nginx/sites-available/nyu-study-spaces > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/nyu-study-spaces /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Allow nginx through firewall
sudo ufw allow 'Nginx Full'

# Start the application
echo "🚀 Starting application..."
cd /opt/nyu-study-spaces
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ Droplet setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Add this droplet's SSH key to GitHub Actions secrets as DROPLET_SSH_KEY"
echo "2. Add the droplet IP address to GitHub Actions secrets as DROPLET_IP"
echo "3. Add the SSH username to GitHub Actions secrets as DROPLET_USER (usually 'root' or your user)"
echo ""
echo "🌐 Your application should be accessible at:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "📊 Check application status:"
echo "   docker-compose ps"
echo "   docker-compose logs -f webapp"
