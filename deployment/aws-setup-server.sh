#!/bin/bash

# OnlyLands AWS EC2 Setup Script
# Run this script on your AWS EC2 instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}==== $1 ====${NC}"
}

print_header "OnlyLands AWS EC2 Setup"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo su -)"
    exit 1
fi

print_header "STEP 1: System Update"
print_status "Updating system packages..."
apt update && apt upgrade -y

print_header "STEP 2: Install Dependencies"
print_status "Installing essential packages..."
apt install -y nginx nodejs npm python3 python3-pip python3-venv git curl wget awscli unzip

# Install Node.js 18
print_status "Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install yarn
print_status "Installing Yarn..."
npm install -g yarn

# Install PM2 for process management
print_status "Installing PM2..."
npm install -g pm2

print_header "STEP 3: Configure Firewall"
print_status "Setting up UFW firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw allow 8001  # Backend port
ufw --force enable

print_header "STEP 4: Create Application Structure"
print_status "Creating application directories..."

APP_DIR="/var/www/onlylands"
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend
mkdir -p $APP_DIR/logs

# Set permissions
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

print_header "STEP 5: Configure Nginx"
print_status "Setting up Nginx configuration..."

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Create OnlyLands Nginx config
cat > /etc/nginx/sites-available/onlylands << 'EOF'
# Frontend server
server {
    listen 80;
    server_name _;  # Will accept any domain for ALB health checks

    root /var/www/onlylands/frontend/build;
    index index.html;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle large file uploads
        client_max_body_size 50M;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }
}

# Backend server (for direct access)
server {
    listen 8001;
    server_name _;

    location / {
        proxy_pass http://localhost:8002;  # Internal backend port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        client_max_body_size 50M;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "backend-healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
ln -s /etc/nginx/sites-available/onlylands /etc/nginx/sites-enabled/

# Test Nginx config
nginx -t

# Start and enable Nginx
systemctl enable nginx
systemctl start nginx

print_header "STEP 6: Install CloudWatch Agent (Optional)"
print_status "Installing CloudWatch Agent for monitoring..."

# Download CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i amazon-cloudwatch-agent.deb

print_header "STEP 7: Create Deployment Scripts"

# Create backend deployment script
cat > /root/deploy-backend.sh << 'EOF'
#!/bin/bash
set -e

APP_DIR="/var/www/onlylands"
cd $APP_DIR/backend

# Activate virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'ECOSYSTEM_EOF'
module.exports = {
  apps: [{
    name: 'onlylands-backend',
    script: 'venv/bin/uvicorn',
    args: 'server:app --host 0.0.0.0 --port 8002',
    cwd: '/var/www/onlylands/backend',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/var/www/onlylands/logs/backend-error.log',
    out_file: '/var/www/onlylands/logs/backend-out.log',
    log_file: '/var/www/onlylands/logs/backend-combined.log'
  }]
};
ECOSYSTEM_EOF

echo "Backend deployment script ready"
EOF

chmod +x /root/deploy-backend.sh

# Create frontend deployment script
cat > /root/deploy-frontend.sh << 'EOF'
#!/bin/bash
set -e

APP_DIR="/var/www/onlylands"
cd $APP_DIR/frontend

# Install dependencies
yarn install

# Build for production
yarn build

# Set correct permissions
chown -R www-data:www-data build/

echo "Frontend deployment script ready"
EOF

chmod +x /root/deploy-frontend.sh

# Create full deployment script
cat > /root/deploy-app.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying OnlyLands Application..."

# Deploy backend
echo "📦 Deploying Backend..."
/root/deploy-backend.sh

# Deploy frontend
echo "🎨 Deploying Frontend..."
/root/deploy-frontend.sh

# Restart services
echo "🔄 Restarting Services..."
pm2 restart ecosystem.config.js || pm2 start /var/www/onlylands/backend/ecosystem.config.js
systemctl reload nginx

echo "✅ Deployment Complete!"

# Show status
pm2 status
systemctl status nginx --no-pager -l
EOF

chmod +x /root/deploy-app.sh

# Create monitoring script
cat > /root/check-status.sh << 'EOF'
#!/bin/bash

echo "=== OnlyLands AWS Status ==="
echo ""

echo "🖥️  System Info:"
echo "Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)"
echo "Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)"
echo ""

echo "🔧 Services Status:"
echo "Nginx: $(systemctl is-active nginx)"
echo "Backend: $(pm2 describe onlylands-backend | grep status || echo 'Not running')"
echo ""

echo "🌐 Port Status:"
echo "Port 80 (HTTP): $(ss -tlnp | grep :80 | head -1 || echo 'Not listening')"
echo "Port 8001 (Backend): $(ss -tlnp | grep :8001 | head -1 || echo 'Not listening')"
echo "Port 8002 (Internal): $(ss -tlnp | grep :8002 | head -1 || echo 'Not listening')"
echo ""

echo "💾 Disk Usage:"
df -h / | tail -1
echo ""

echo "🧠 Memory Usage:"
free -h | head -2
echo ""

echo "📊 Recent Backend Logs:"
tail -n 5 /var/www/onlylands/logs/backend-combined.log 2>/dev/null || echo "No backend logs yet"
EOF

chmod +x /root/check-status.sh

print_header "STEP 8: Configure Log Rotation"
cat > /etc/logrotate.d/onlylands << 'EOF'
/var/www/onlylands/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    postrotate
        pm2 reloadLogs
    endscript
}
EOF

print_header "STEP 9: AWS CLI Configuration"
print_status "Configuring AWS CLI..."

# Create AWS credentials template (user will need to update)
mkdir -p /root/.aws
cat > /root/.aws/credentials << 'EOF'
[default]
aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
EOF

cat > /root/.aws/config << 'EOF'
[default]
region = eu-north-1
output = json
EOF

# Set permissions
chmod 600 /root/.aws/credentials
chmod 600 /root/.aws/config

print_warning "⚠️ Update AWS credentials in /root/.aws/credentials with your actual keys"

print_header "SETUP COMPLETE!"
print_status "AWS EC2 server setup completed successfully!"
echo ""
print_warning "Next Steps:"
echo "1. Upload your application files to /var/www/onlylands/"
echo "2. Run: /root/deploy-app.sh"
echo "3. Set up your Load Balancer and Route 53"
echo "4. Configure SSL certificates"
echo ""
print_status "Useful commands:"
echo "  - Check status: /root/check-status.sh"
echo "  - Deploy app: /root/deploy-app.sh"
echo "  - View logs: tail -f /var/www/onlylands/logs/backend-combined.log"
echo "  - PM2 status: pm2 status"
echo "  - Nginx status: systemctl status nginx"

# Show server info
echo ""
print_header "SERVER INFORMATION"
echo "Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)"
echo "Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "Private IP: $(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)"