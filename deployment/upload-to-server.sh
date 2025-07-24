#!/bin/bash

# Quick deployment script for uploading OnlyLands files to DigitalOcean
# Run this on your LOCAL machine to upload files to the server

# Configuration - Update these values
SERVER_IP="YOUR_DROPLET_IP"        # Replace with your DigitalOcean droplet IP
SSH_KEY_PATH="~/.ssh/id_rsa"       # Path to your SSH private key
LOCAL_APP_PATH="/app"              # Path to your local OnlyLands application

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

# Check if configuration is updated
if [ "$SERVER_IP" = "YOUR_DROPLET_IP" ]; then
    print_error "Please update the SERVER_IP in this script with your actual droplet IP"
    exit 1
fi

print_header "OnlyLands File Upload to DigitalOcean"

# Check if local app directory exists
if [ ! -d "$LOCAL_APP_PATH" ]; then
    print_error "Local app directory not found: $LOCAL_APP_PATH"
    exit 1
fi

# Check if SSH key exists
if [ ! -f "${SSH_KEY_PATH/\~/$HOME}" ]; then
    print_error "SSH key not found: $SSH_KEY_PATH"
    print_warning "You may need to use password authentication instead"
fi

# Test SSH connection
print_status "Testing SSH connection to $SERVER_IP..."
if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o BatchMode=yes root@$SERVER_IP exit; then
    print_status "SSH connection successful"
else
    print_error "SSH connection failed. Please check:"
    echo "  - Server IP: $SERVER_IP"
    echo "  - SSH key: $SSH_KEY_PATH"
    echo "  - Server is running and accessible"
    exit 1
fi

print_header "STEP 1: Prepare Local Files"

# Create temporary directory for clean files
TEMP_DIR="/tmp/onlylands-deploy"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Copy application files
print_status "Copying application files..."
cp -r $LOCAL_APP_PATH/* $TEMP_DIR/

# Remove development-specific files
print_status "Cleaning up development files..."
find $TEMP_DIR -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find $TEMP_DIR -name "*.pyc" -delete 2>/dev/null || true
find $TEMP_DIR -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find $TEMP_DIR -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
find $TEMP_DIR -name ".env" -delete 2>/dev/null || true

# Create production-ready directory structure
mkdir -p $TEMP_DIR/deployment

print_header "STEP 2: Upload Files to Server"

# Upload application files
print_status "Uploading backend files..."
rsync -avz -e "ssh -i $SSH_KEY_PATH" $TEMP_DIR/backend/ root@$SERVER_IP:/var/www/onlylands/backend/

print_status "Uploading frontend files..."
rsync -avz -e "ssh -i $SSH_KEY_PATH" $TEMP_DIR/frontend/ root@$SERVER_IP:/var/www/onlylands/frontend/

# Upload deployment scripts
print_status "Uploading deployment scripts..."
rsync -avz -e "ssh -i $SSH_KEY_PATH" $TEMP_DIR/deployment/ root@$SERVER_IP:/root/

print_header "STEP 3: Set Permissions and Deploy"

# Execute deployment script on server
print_status "Running deployment script on server..."
ssh -i "$SSH_KEY_PATH" root@$SERVER_IP << 'EOF'
    chmod +x /root/deploy-app.sh
    /root/deploy-app.sh
EOF

if [ $? -eq 0 ]; then
    print_status "Deployment completed successfully!"
else
    print_error "Deployment failed. Check server logs."
    exit 1
fi

print_header "STEP 4: Final Instructions"

echo ""
print_status "🎉 Files uploaded and deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure DNS records for onlylands.in:"
echo "   - A record: @ → $SERVER_IP"
echo "   - A record: www → $SERVER_IP"  
echo "   - A record: api → $SERVER_IP"
echo ""
echo "2. Wait 5-10 minutes for DNS propagation"
echo ""
echo "3. Set up SSL certificate (run on server):"
echo "   ssh root@$SERVER_IP"
echo "   certbot --nginx -d onlylands.in -d www.onlylands.in -d api.onlylands.in"
echo ""
echo "4. Test your website:"
echo "   - Frontend: https://onlylands.in"
echo "   - API: https://api.onlylands.in/docs"
echo ""
echo "Server Management Commands:"
echo "   ssh root@$SERVER_IP \"/root/check-onlylands.sh\"  # Check status"
echo "   ssh root@$SERVER_IP \"journalctl -u onlylands-backend -f\"  # View logs"
echo "   ssh root@$SERVER_IP \"/root/backup-onlylands.sh\"  # Backup data"
echo ""

# Clean up temporary files
rm -rf $TEMP_DIR
print_status "Temporary files cleaned up"

echo ""
print_status "🚀 Your OnlyLands application is now live!"