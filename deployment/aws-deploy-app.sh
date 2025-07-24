#!/bin/bash

# OnlyLands AWS Application Deployment Script
# Run this after uploading your application files

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

print_header "OnlyLands AWS Application Deployment"

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

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Create production environment file
print_status "Creating production environment configuration..."
cat > .env << 'EOF'
# MongoDB Atlas Configuration (UPDATE THIS)
MONGO_URL="YOUR_MONGODB_CONNECTION_STRING"
DB_NAME="onlylands_db"

# Twilio Configuration (UPDATE THESE)
TWILIO_ACCOUNT_SID="YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN="YOUR_TWILIO_AUTH_TOKEN"
TWILIO_VERIFY_SERVICE_SID="YOUR_TWILIO_VERIFY_SERVICE_SID"
TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"

# Razorpay Configuration (UPDATE THESE)
RAZORPAY_KEY_ID="YOUR_RAZORPAY_KEY_ID"
RAZORPAY_KEY_SECRET="YOUR_RAZORPAY_KEY_SECRET"

# AWS S3 Configuration (UPDATE THESE)
AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
AWS_BUCKET_NAME="YOUR_BUCKET_NAME"
AWS_REGION="YOUR_AWS_REGION"
EOF

print_warning "⚠️  IMPORTANT: Update all credentials in .env with your actual API keys!"
print_warning "Check CREDENTIALS.md file for the actual values to use."

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create PM2 ecosystem configuration
print_status "Creating PM2 configuration..."
cat > ecosystem.config.js << 'EOF'
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

# Set correct permissions
chown -R www-data:www-data build/
chmod -R 755 build/

print_header "STEP 3: Start Services"

# Start backend with PM2
print_status "Starting backend service..."
cd $APP_DIR/backend
pm2 delete onlylands-backend 2>/dev/null || true
pm2 start ecosystem.config.js

# Save PM2 process list
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
if curl -s http://localhost:8002/docs > /dev/null; then
    print_status "✅ Backend is responding"
else
    print_warning "❌ Backend health check failed"
    pm2 logs onlylands-backend --lines 10
fi

# Check Nginx
print_status "Checking Nginx..."
if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx is not running"
    systemctl status nginx
fi

print_header "STEP 5: AWS Load Balancer Setup Instructions"

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)

echo ""
print_status "🎯 Your server is ready! Now set up AWS Load Balancer:"
echo ""
echo "📋 Instance Information:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Private IP: $PRIVATE_IP"
echo ""
echo "🔧 Load Balancer Target Groups:"
echo "  Frontend: Register $INSTANCE_ID on port 80"
echo "  Backend: Register $INSTANCE_ID on port 8001"
echo ""
echo "🌐 Health Check Endpoints:"
echo "  Frontend: http://$PUBLIC_IP/health"
echo "  Backend: http://$PUBLIC_IP:8001/health"
echo ""

print_header "STEP 6: MongoDB Setup Reminder"
echo ""
print_warning "🔗 Don't forget to set up MongoDB Atlas:"
echo "1. Create MongoDB Atlas cluster (M0 free tier or M2 $9/month)"
echo "2. Create database user and whitelist this IP: $PUBLIC_IP"
echo "3. Update MONGO_URL in /var/www/onlylands/backend/.env"
echo "4. Restart backend: pm2 restart onlylands-backend"
echo ""

print_header "DEPLOYMENT SUMMARY"
echo ""
print_status "🎉 OnlyLands AWS deployment completed!"
echo ""
echo "📊 Service Status:"
pm2 list
echo ""
systemctl status nginx --no-pager -l | head -5
echo ""
echo "📝 Next Steps:"
echo "1. Set up MongoDB Atlas and update connection string"
echo "2. Create AWS Application Load Balancer"
echo "3. Configure Route 53 DNS records"
echo "4. Set up SSL certificate in ACM"
echo "5. Test complete application flow"
echo ""
echo "🔍 Monitoring Commands:"
echo "  Status: /root/check-status.sh"
echo "  Backend logs: pm2 logs onlylands-backend"
echo "  Nginx logs: tail -f /var/log/nginx/access.log"
echo "  Restart backend: pm2 restart onlylands-backend"
echo ""

print_status "📍 Your application will be live at: https://onlylands.in"
print_status "📍 API documentation: https://api.onlylands.in/docs"