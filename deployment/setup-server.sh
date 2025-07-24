#!/bin/bash

# OnlyLands DigitalOcean Deployment Script
# This script sets up the complete production environment

set -e  # Exit on any error

echo "🚀 Starting OnlyLands Deployment on DigitalOcean..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

print_header "STEP 1: System Update and Dependencies"

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
print_status "Installing essential packages..."
apt install -y nginx nodejs npm python3 python3-pip python3-venv git curl wget gnupg2 software-properties-common ufw

# Install Node.js 18
print_status "Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install yarn
print_status "Installing Yarn..."
npm install -g yarn

# Install MongoDB
print_header "STEP 2: MongoDB Installation"
print_status "Installing MongoDB..."

# Import MongoDB GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
apt update
apt install -y mongodb-org

# Start and enable MongoDB
systemctl start mongod
systemctl enable mongod

print_status "MongoDB installed and started"

# Configure firewall
print_header "STEP 3: Firewall Configuration"
print_status "Configuring UFW firewall..."

ufw --force reset
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw allow 27017  # MongoDB (only if needed for external access)
ufw --force enable

print_status "Firewall configured"

# Create application directory
print_header "STEP 4: Application Setup"
print_status "Creating application directory..."

APP_DIR="/var/www/onlylands"
mkdir -p $APP_DIR
cd $APP_DIR

# You'll need to upload your application files here
# For now, we'll create the directory structure
mkdir -p backend frontend

print_status "Application directory created at $APP_DIR"

# Backend setup
print_header "STEP 5: Backend Setup"
print_status "Setting up Python virtual environment..."

cd $APP_DIR/backend
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt if it doesn't exist
cat > requirements.txt << 'EOF'
fastapi==0.110.1
uvicorn==0.25.0
boto3>=1.34.129
requests-oauthlib>=2.0.0
cryptography>=42.0.8
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
email-validator>=2.2.0
pyjwt>=2.10.1
passlib>=1.7.4
tzdata>=2024.2
motor==3.3.1
pytest>=8.0.0
black>=24.1.1
isort>=5.13.2
flake8>=7.0.0
mypy>=1.8.0
python-jose>=3.3.0
requests>=2.31.0
pandas>=2.2.0
numpy>=1.26.0
python-multipart>=0.0.9
jq>=1.6.0
typer>=0.9.0
twilio>=8.0.0
razorpay>=1.3.0
EOF

# Install Python dependencies
pip install -r requirements.txt

# Create production environment file
print_status "Creating production environment file..."
cat > .env << 'EOF'
MONGO_URL="mongodb://localhost:27017"
DB_NAME="onlylands_db"

# Twilio Configuration (UPDATE WITH YOUR CREDENTIALS)
TWILIO_ACCOUNT_SID="YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN="YOUR_TWILIO_AUTH_TOKEN"
TWILIO_VERIFY_SERVICE_SID="YOUR_TWILIO_VERIFY_SERVICE_SID"
TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"

# Razorpay Configuration (UPDATE WITH YOUR CREDENTIALS)  
RAZORPAY_KEY_ID="YOUR_RAZORPAY_KEY_ID"
RAZORPAY_KEY_SECRET="YOUR_RAZORPAY_KEY_SECRET"

# AWS S3 Configuration (UPDATE WITH YOUR CREDENTIALS)
AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
AWS_BUCKET_NAME="YOUR_BUCKET_NAME"
AWS_REGION="YOUR_AWS_REGION"
EOF

# Systemd service for backend
print_header "STEP 6: Creating Systemd Service"
print_status "Creating systemd service for backend..."

cat > /etc/systemd/system/onlylands-backend.service << 'EOF'
[Unit]
Description=OnlyLands FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/onlylands/backend
Environment=PATH=/var/www/onlylands/backend/venv/bin
ExecStart=/var/www/onlylands/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable the service (but don't start yet, need the server.py file)
systemctl enable onlylands-backend

# Nginx configuration
print_header "STEP 7: Nginx Configuration"
print_status "Configuring Nginx..."

cat > /etc/nginx/sites-available/onlylands << 'EOF'
# Backend API server
server {
    listen 80;
    server_name api.onlylands.in;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle large file uploads
        client_max_body_size 50M;
        
        # Timeout settings
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }
}

# Frontend server
server {
    listen 80;
    server_name onlylands.in www.onlylands.in;

    root /var/www/onlylands/frontend/build;
    index index.html;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoint fallback
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
ln -s /etc/nginx/sites-available/onlylands /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Start Nginx
systemctl enable nginx
systemctl start nginx

# SSL/HTTPS Setup
print_header "STEP 8: SSL Certificate Setup"
print_status "Installing Certbot for SSL certificates..."

apt install -y certbot python3-certbot-nginx

print_status "SSL tools installed. You'll need to run certbot after DNS is configured."

# Backup script
print_header "STEP 9: Backup Script Setup"
print_status "Creating backup script..."

mkdir -p /root/backups

cat > /root/backup-onlylands.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

echo "Starting backup at $DATE"

# Backup MongoDB
mongodump --out $BACKUP_DIR/mongo_$DATE

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /var/www/onlylands

# Backup Nginx configuration
tar -czf $BACKUP_DIR/nginx_$DATE.tar.gz /etc/nginx/sites-available/onlylands

# Keep only last 7 backups
find $BACKUP_DIR -name "mongo_*" -mtime +7 -delete
find $BACKUP_DIR -name "app_*" -mtime +7 -delete
find $BACKUP_DIR -name "nginx_*" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup-onlylands.sh

# Schedule daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup-onlylands.sh") | crontab -

# Monitoring script
print_status "Creating monitoring script..."

cat > /root/check-onlylands.sh << 'EOF'
#!/bin/bash

# Check if services are running
echo "=== OnlyLands Service Status ==="
echo "Backend Service:"
systemctl is-active onlylands-backend

echo "MongoDB:"
systemctl is-active mongod

echo "Nginx:"
systemctl is-active nginx

echo "=== Port Status ==="
echo "Port 8001 (Backend):"
ss -tlnp | grep :8001 || echo "Not listening"

echo "Port 80 (HTTP):"
ss -tlnp | grep :80 || echo "Not listening"

echo "Port 443 (HTTPS):"
ss -tlnp | grep :443 || echo "Not listening"

echo "Port 27017 (MongoDB):"
ss -tlnp | grep :27017 || echo "Not listening"

echo "=== Disk Usage ==="
df -h

echo "=== Memory Usage ==="
free -h

echo "=== Recent Backend Logs ==="
journalctl -u onlylands-backend --no-pager -n 5
EOF

chmod +x /root/check-onlylands.sh

# Create deployment info file
print_header "STEP 10: Creating Deployment Info"

cat > /root/deployment-info.txt << EOF
OnlyLands Deployment Information
===============================
Deployment Date: $(date)
Server IP: $(curl -s ifconfig.me)
Domain: onlylands.in

Application Directory: /var/www/onlylands
Backend Service: onlylands-backend
Database: MongoDB (local)

Important Commands:
- Check services: /root/check-onlylands.sh
- Backend logs: journalctl -u onlylands-backend -f
- Nginx logs: tail -f /var/log/nginx/access.log
- MongoDB logs: tail -f /var/log/mongodb/mongod.log
- Backup: /root/backup-onlylands.sh

Next Steps:
1. Upload your application files to /var/www/onlylands/
2. Configure DNS for onlylands.in to point to this server
3. Run: certbot --nginx -d onlylands.in -d www.onlylands.in -d api.onlylands.in
4. Start backend: systemctl start onlylands-backend
5. Build frontend and reload nginx
EOF

print_header "DEPLOYMENT COMPLETE!"
print_status "Server setup completed successfully!"
print_warning "Next steps:"
echo "1. Upload your application files to /var/www/onlylands/"
echo "2. Configure DNS records for onlylands.in"
echo "3. Run SSL certificate setup"
echo "4. Start the backend service"
echo ""
print_status "Check /root/deployment-info.txt for detailed information"
print_status "Run /root/check-onlylands.sh to check service status"

echo ""
print_header "QUICK COMMANDS"
echo "Check status: /root/check-onlylands.sh"
echo "Backend logs: journalctl -u onlylands-backend -f"
echo "Restart backend: systemctl restart onlylands-backend"
echo "Reload nginx: systemctl reload nginx"
echo "Backup: /root/backup-onlylands.sh"