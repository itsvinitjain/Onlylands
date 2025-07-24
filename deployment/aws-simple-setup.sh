#!/bin/bash

# OnlyLands Simple AWS EC2 Deployment (No Load Balancer)
# For EC2 in Mumbai (ap-south-1)

set -e

# Colors
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

print_header "OnlyLands Simple AWS Deployment (Mumbai)"

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
apt install -y nginx nodejs npm python3 python3-pip python3-venv git curl wget awscli unzip snapd

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

# Install Certbot for SSL
print_status "Installing Certbot for SSL..."
snap install --classic certbot
ln -s /snap/bin/certbot /usr/bin/certbot

print_header "STEP 3: Configure Firewall"
print_status "Setting up UFW firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
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

print_header "STEP 5: Configure Nginx for Direct SSL"
print_status "Setting up Nginx configuration..."

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Create OnlyLands Nginx config (HTTP first, will add SSL later)
cat > /etc/nginx/sites-available/onlylands << 'EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name onlylands.in www.onlylands.in api.onlylands.in;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Frontend server
server {
    listen 443 ssl http2;
    server_name onlylands.in www.onlylands.in;

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/onlylands.in/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/onlylands.in/privkey.pem;

    root /var/www/onlylands/frontend/build;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
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

# HTTPS API server
server {
    listen 443 ssl http2;
    server_name api.onlylands.in;

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/onlylands.in/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/onlylands.in/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        client_max_body_size 50M;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
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

print_header "STEP 6: Configure AWS CLI"
print_status "Setting up AWS CLI..."

mkdir -p /root/.aws
cat > /root/.aws/credentials << 'EOF'
[default]
aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
EOF

cat > /root/.aws/config << 'EOF'
[default]
region = ap-south-1
output = json
EOF

chmod 600 /root/.aws/credentials
chmod 600 /root/.aws/config

print_warning "⚠️ Update AWS credentials in /root/.aws/credentials"

print_header "STEP 7: Create Deployment Scripts"

# Backend deployment script
cat > /root/deploy-backend.sh << 'EOF'
#!/bin/bash
set -e

APP_DIR="/var/www/onlylands"
cd $APP_DIR/backend

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'ECOSYSTEM_EOF'
module.exports = {
  apps: [{
    name: 'onlylands-backend',
    script: 'venv/bin/uvicorn',
    args: 'server:app --host 0.0.0.0 --port 8001',
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

# Frontend deployment script  
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

# SSL setup script
cat > /root/setup-ssl.sh << 'EOF'
#!/bin/bash
set -e

echo "🔒 Setting up SSL certificates..."

# Stop nginx temporarily
systemctl stop nginx

# Get certificates for all domains
certbot certonly --standalone \
  -d onlylands.in \
  -d www.onlylands.in \
  -d api.onlylands.in \
  --non-interactive \
  --agree-tos \
  --email admin@onlylands.in

# Start nginx
systemctl start nginx

# Test certificate renewal
certbot renew --dry-run

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx" | crontab -

echo "✅ SSL certificates installed successfully!"
EOF

chmod +x /root/setup-ssl.sh

# Full deployment script
cat > /root/deploy-app.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying OnlyLands Application..."

# Check if files exist
if [ ! -f "/var/www/onlylands/backend/server.py" ]; then
    echo "❌ Backend files not found. Please upload application files first."
    exit 1
fi

if [ ! -f "/var/www/onlylands/frontend/package.json" ]; then
    echo "❌ Frontend files not found. Please upload application files first."
    exit 1
fi

# Deploy backend
echo "📦 Deploying Backend..."
/root/deploy-backend.sh

# Deploy frontend
echo "🎨 Deploying Frontend..."
/root/deploy-frontend.sh

# Start/restart services
echo "🔄 Starting Services..."
cd /var/www/onlylands/backend
pm2 delete onlylands-backend 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Reload nginx
systemctl reload nginx

echo "✅ Deployment Complete!"

# Show status
echo ""
echo "📊 Service Status:"
pm2 list
systemctl status nginx --no-pager -l | head -3

echo ""
echo "🌐 Your app will be available at:"
echo "  - https://onlylands.in (after SSL setup)"
echo "  - https://api.onlylands.in/docs (after SSL setup)"
echo ""
echo "Next steps:"
echo "1. Configure GoDaddy DNS records"
echo "2. Wait for DNS propagation (5-10 minutes)"
echo "3. Run: /root/setup-ssl.sh"
EOF

chmod +x /root/deploy-app.sh

# Status check script
cat > /root/check-status.sh << 'EOF'
#!/bin/bash

echo "=== OnlyLands Simple AWS Status ==="
echo ""

echo "🖥️  Server Info:"
echo "Public IP: 51.21.198.121"
echo "Region: Mumbai (ap-south-1)"
echo "Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo 'N/A')"
echo ""

echo "🔧 Services Status:"
echo "Nginx: $(systemctl is-active nginx)"
echo "Backend: $(pm2 describe onlylands-backend 2>/dev/null | grep -o 'online\|stopped\|errored' || echo 'Not running')"
echo ""

echo "🌐 Port Status:"
echo "Port 80 (HTTP): $(ss -tlnp | grep :80 | head -1 || echo 'Not listening')"
echo "Port 443 (HTTPS): $(ss -tlnp | grep :443 | head -1 || echo 'Not listening')"  
echo "Port 8001 (Backend): $(ss -tlnp | grep :8001 | head -1 || echo 'Not listening')"
echo ""

echo "💾 Disk Usage:"
df -h / | tail -1
echo ""

echo "🧠 Memory Usage:"
free -h | head -2
echo ""

echo "🔒 SSL Status:"
if [ -f "/etc/letsencrypt/live/onlylands.in/fullchain.pem" ]; then
    echo "SSL Certificate: ✅ Installed"
    echo "Expires: $(openssl x509 -enddate -noout -in /etc/letsencrypt/live/onlylands.in/fullchain.pem)"
else
    echo "SSL Certificate: ❌ Not installed"
fi
echo ""

echo "📊 Recent Backend Logs:"
tail -n 5 /var/www/onlylands/logs/backend-combined.log 2>/dev/null || echo "No backend logs yet"
EOF

chmod +x /root/check-status.sh

print_header "SETUP COMPLETE!"
print_status "Simple AWS EC2 server setup completed successfully!"

echo ""
print_status "🌐 Server Information:"
echo "  Public IP: 51.21.198.121"
echo "  Region: Mumbai (ap-south-1)"
echo "  Domain: onlylands.in"
echo ""

print_warning "📋 Next Steps:"
echo "1. Upload your application files to /var/www/onlylands/"
echo "2. Configure GoDaddy DNS records"
echo "3. Run: /root/deploy-app.sh"
echo "4. Run: /root/setup-ssl.sh (after DNS propagation)"
echo ""

print_status "🔧 Useful Commands:"
echo "  - Check status: /root/check-status.sh"
echo "  - Deploy app: /root/deploy-app.sh" 
echo "  - Setup SSL: /root/setup-ssl.sh"
echo "  - Backend logs: pm2 logs onlylands-backend"
echo "  - Nginx logs: tail -f /var/log/nginx/access.log"