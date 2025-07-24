#!/bin/bash

# OnlyLands Simple Application Deployment
# Run after uploading application files

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

print_header "OnlyLands Simple Deployment"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo su -)"
    exit 1
fi

APP_DIR="/var/www/onlylands"

# Check if application files exist
if [ ! -f "$APP_DIR/backend/server.py" ]; then
    print_error "Backend files not found. Please upload your application files first."
    echo "Expected: $APP_DIR/backend/server.py"
    exit 1
fi

if [ ! -f "$APP_DIR/frontend/package.json" ]; then
    print_error "Frontend files not found. Please upload your application files first."
    echo "Expected: $APP_DIR/frontend/package.json"
    exit 1
fi

print_header "STEP 1: Backend Configuration"

cd $APP_DIR/backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Create production environment file with MongoDB Atlas
print_status "Creating production environment configuration..."
cat > .env << 'EOF'
# MongoDB Atlas Configuration
MONGO_URL="YOUR_MONGODB_CONNECTION_STRING_HERE"
DB_NAME="onlylands_db"

# Twilio Configuration
TWILIO_ACCOUNT_SID="YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN="YOUR_TWILIO_AUTH_TOKEN"
TWILIO_VERIFY_SERVICE_SID="YOUR_TWILIO_VERIFY_SERVICE_SID"
TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"

# Razorpay Configuration
RAZORPAY_KEY_ID="YOUR_RAZORPAY_KEY_ID"
RAZORPAY_KEY_SECRET="YOUR_RAZORPAY_KEY_SECRET"

# AWS S3 Configuration
AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
AWS_BUCKET_NAME="YOUR_BUCKET_NAME"
AWS_REGION="YOUR_AWS_REGION"
EOF

print_warning "🔑 IMPORTANT: Please update ALL credentials in .env file!"
print_warning "Check the CREDENTIALS.md file for actual values to use"

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create PM2 ecosystem file
print_status "Creating PM2 configuration..."
cat > ecosystem.config.js << 'EOF'
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
EOF

print_header "STEP 2: Frontend Configuration"

cd $APP_DIR/frontend

# Create production environment file
print_status "Creating frontend environment configuration..."
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=https://api.onlylands.in
EOF

# Install dependencies
print_status "Installing frontend dependencies..."
yarn install

# Build production version
print_status "Building frontend for production..."
yarn build

# Set permissions
chown -R www-data:www-data build/
chmod -R 755 build/

print_header "STEP 3: Start Services"

# Start backend with PM2
print_status "Starting backend service..."
cd $APP_DIR/backend
pm2 delete onlylands-backend 2>/dev/null || true
pm2 start ecosystem.config.js

# Save PM2 process list and set up auto-start
pm2 save
pm2 startup

# Reload Nginx
print_status "Reloading Nginx..."
nginx -t && systemctl reload nginx

print_header "STEP 4: Health Check"

# Wait for services to start
sleep 5

# Check backend health
print_status "Checking backend health..."
if curl -s http://localhost:8001/docs > /dev/null; then
    print_status "✅ Backend is responding"
else
    print_warning "❌ Backend health check failed"
    print_warning "Check MongoDB connection string in .env file"
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx is not running"
fi

print_header "STEP 5: GoDaddy DNS Configuration Guide"

print_status "📋 Configure these DNS records in GoDaddy:"
echo ""
echo "Go to GoDaddy DNS Management and add:"
echo ""
echo "Type: A    Name: @      Value: 51.21.198.121    TTL: 600"
echo "Type: A    Name: www    Value: 51.21.198.121    TTL: 600"  
echo "Type: A    Name: api    Value: 51.21.198.121    TTL: 600"
echo ""
print_warning "Wait 5-10 minutes for DNS propagation before setting up SSL"

print_header "DEPLOYMENT SUMMARY"

echo ""
print_status "🎉 OnlyLands simple deployment completed!"
echo ""
echo "📊 Service Status:"
pm2 list
echo ""
systemctl status nginx --no-pager -l | head -3
echo ""
echo "🌐 Application URLs (after SSL setup):"
echo "  Frontend: https://onlylands.in"
echo "  API: https://api.onlylands.in/docs"
echo "  Admin: https://onlylands.in (admin panel button)"
echo ""
echo "📋 Immediate Next Steps:"
echo "1. 🔑 Update MongoDB password in: nano /var/www/onlylands/backend/.env"
echo "2. 🌐 Configure GoDaddy DNS records (shown above)"
echo "3. ⏰ Wait 5-10 minutes for DNS propagation"
echo "4. 🔒 Run SSL setup: /root/setup-ssl.sh"
echo "5. 🔄 Restart backend: pm2 restart onlylands-backend"
echo ""
echo "🔍 Monitoring Commands:"
echo "  Status: /root/check-status.sh"
echo "  Backend logs: pm2 logs onlylands-backend"
echo "  Nginx logs: tail -f /var/log/nginx/access.log"
echo "  Edit MongoDB: nano /var/www/onlylands/backend/.env"
echo ""

print_warning "⚠️  Remember to:"
echo "- Update MongoDB password before testing"
echo "- Configure GoDaddy DNS records"
echo "- Wait for DNS propagation before SSL setup"

print_status "💰 Estimated Monthly Cost: $17-26 (EC2 + MongoDB Atlas)"
print_status "🚀 Your app will be live at: https://onlylands.in"