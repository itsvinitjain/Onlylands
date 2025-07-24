#!/bin/bash

# OnlyLands Application Deployment Script
# Run this script after the server setup is complete and you've uploaded your files

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

APP_DIR="/var/www/onlylands"

print_header "OnlyLands Application Deployment"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    print_error "Application directory $APP_DIR not found. Please run setup-server.sh first."
    exit 1
fi

# Check if backend files exist
if [ ! -f "$APP_DIR/backend/server.py" ]; then
    print_error "Backend files not found. Please upload your application files first."
    echo "Expected: $APP_DIR/backend/server.py"
    exit 1
fi

# Check if frontend files exist
if [ ! -f "$APP_DIR/frontend/package.json" ]; then
    print_error "Frontend files not found. Please upload your application files first."
    echo "Expected: $APP_DIR/frontend/package.json"
    exit 1
fi

print_header "STEP 1: Backend Deployment"

# Navigate to backend directory
cd $APP_DIR/backend

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
print_status "Installing backend dependencies..."
pip install -r requirements.txt

# Set correct permissions
chown -R root:root $APP_DIR
chmod -R 755 $APP_DIR

print_status "Backend setup complete"

print_header "STEP 2: Frontend Deployment"

# Navigate to frontend directory
cd $APP_DIR/frontend

# Create production environment file
print_status "Creating frontend production environment..."
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://api.onlylands.in
EOF

# Install dependencies
print_status "Installing frontend dependencies..."
yarn install

# Build production version
print_status "Building frontend for production..."
yarn build

# Set correct permissions for nginx
chown -R www-data:www-data $APP_DIR/frontend/build

print_status "Frontend build complete"

print_header "STEP 3: Service Management"

# Start/restart backend service
print_status "Starting backend service..."
systemctl daemon-reload
systemctl restart onlylands-backend
systemctl enable onlylands-backend

# Wait a moment for service to start
sleep 3

# Check if backend is running
if systemctl is-active --quiet onlylands-backend; then
    print_status "Backend service is running"
else
    print_error "Backend service failed to start"
    journalctl -u onlylands-backend --no-pager -n 10
    exit 1
fi

# Reload nginx
print_status "Reloading Nginx..."
nginx -t && systemctl reload nginx

print_header "STEP 4: Health Check"

# Test backend API
print_status "Testing backend API..."
sleep 2

if curl -s http://localhost:8001/docs > /dev/null; then
    print_status "Backend API is responding"
else
    print_warning "Backend API is not responding yet. Check logs with: journalctl -u onlylands-backend -f"
fi

# Test MongoDB connection
print_status "Testing MongoDB connection..."
if systemctl is-active --quiet mongod; then
    print_status "MongoDB is running"
    
    # Test MongoDB connection
    if mongo --eval "db.runCommand('ping').ok" localhost/onlylands_db > /dev/null 2>&1; then
        print_status "MongoDB connection successful"
    else
        print_warning "MongoDB connection test failed"
    fi
else
    print_error "MongoDB is not running"
    systemctl start mongod
fi

print_header "STEP 5: SSL Certificate Setup"

# Check if domain is pointing to this server
SERVER_IP=$(curl -s ifconfig.me)
print_status "Server IP: $SERVER_IP"

# Function to check DNS
check_dns() {
    local domain=$1
    local dns_ip=$(dig +short $domain | head -n1)
    
    if [ "$dns_ip" = "$SERVER_IP" ]; then
        print_status "$domain DNS is correctly pointing to this server"
        return 0
    else
        print_warning "$domain DNS is not pointing to this server (points to: $dns_ip)"
        return 1
    fi
}

print_status "Checking DNS configuration..."

DNS_READY=true
check_dns "onlylands.in" || DNS_READY=false
check_dns "www.onlylands.in" || DNS_READY=false
check_dns "api.onlylands.in" || DNS_READY=false

if [ "$DNS_READY" = true ]; then
    print_status "All DNS records are correctly configured"
    print_status "Setting up SSL certificates..."
    
    # Get SSL certificates
    certbot --nginx --non-interactive --agree-tos --email admin@onlylands.in \
        -d onlylands.in -d www.onlylands.in -d api.onlylands.in
    
    if [ $? -eq 0 ]; then
        print_status "SSL certificates installed successfully"
        
        # Update frontend environment for HTTPS
        cd $APP_DIR/frontend
        cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://api.onlylands.in
EOF
        
        # Rebuild frontend with HTTPS URLs
        yarn build
        chown -R www-data:www-data $APP_DIR/frontend/build
        systemctl reload nginx
        
        print_status "Frontend updated for HTTPS"
    else
        print_warning "SSL certificate installation failed. You can retry manually later."
    fi
else
    print_warning "DNS not ready. Please configure DNS records and run SSL setup manually:"
    echo "certbot --nginx -d onlylands.in -d www.onlylands.in -d api.onlylands.in"
fi

print_header "STEP 6: Final Configuration"

# Set up log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/onlylands << 'EOF'
/var/log/nginx/*onlylands* {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# Create monitoring cron job
print_status "Setting up monitoring..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/check-onlylands.sh > /var/log/onlylands-monitor.log 2>&1") | crontab -

print_header "DEPLOYMENT SUMMARY"

echo ""
print_status "🎉 OnlyLands deployment completed successfully!"
echo ""
echo "Application URLs:"
echo "  Frontend: https://onlylands.in (or http://onlylands.in if SSL not ready)"
echo "  API Docs: https://api.onlylands.in/docs"
echo "  Admin: https://onlylands.in (admin panel button in the app)"
echo ""
echo "Service Status:"
systemctl is-active onlylands-backend && echo "  ✅ Backend: Running" || echo "  ❌ Backend: Not running"
systemctl is-active nginx && echo "  ✅ Nginx: Running" || echo "  ❌ Nginx: Not running"
systemctl is-active mongod && echo "  ✅ MongoDB: Running" || echo "  ❌ MongoDB: Not running"
echo ""
echo "Useful Commands:"
echo "  Check status: /root/check-onlylands.sh"
echo "  Backend logs: journalctl -u onlylands-backend -f"
echo "  Nginx logs: tail -f /var/log/nginx/access.log"
echo "  Restart backend: systemctl restart onlylands-backend"
echo "  Backup data: /root/backup-onlylands.sh"
echo ""

if [ "$DNS_READY" = true ]; then
    print_status "🌐 Your website should be live at https://onlylands.in"
else
    print_warning "⚠️ Configure DNS records first, then run SSL setup"
fi

print_status "📋 Check /root/deployment-info.txt for more details"