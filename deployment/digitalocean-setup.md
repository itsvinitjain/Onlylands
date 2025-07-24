# OnlyLands Deployment Guide - DigitalOcean

## Complete setup guide for deploying OnlyLands to DigitalOcean with custom domain onlylands.in

### Prerequisites
- DigitalOcean account
- Domain onlylands.in (access to DNS settings)
- Local machine with Docker installed
- GitHub account (recommended)

## Step 1: Create DigitalOcean Infrastructure

### 1.1 Create Droplet
1. **Go to DigitalOcean Console** → Create → Droplets
2. **Choose Image:** Ubuntu 22.04 LTS
3. **Choose Size:** 
   - **Basic Plan:** $12/month (2GB RAM, 1 vCPU, 50GB SSD)
   - **Recommended:** $18/month (2GB RAM, 2 vCPU, 60GB SSD)
4. **Choose Region:** Closest to your users (e.g., Bangalore if targeting India)
5. **Authentication:** Add your SSH key or use password
6. **Hostname:** onlylands-prod
7. **Tags:** production, onlylands
8. **Click Create Droplet**

### 1.2 Set up MongoDB Database
**Option A: DigitalOcean Managed MongoDB (Recommended)**
1. Go to **Databases** → Create Database
2. **Engine:** MongoDB
3. **Plan:** Basic ($15/month for 1GB RAM)
4. **Region:** Same as your droplet
5. **Database Name:** onlylands-db
6. **Click Create Database**
7. **Copy the connection string** for later

**Option B: Self-hosted MongoDB (Budget option)**
- We'll install MongoDB on the same droplet

## Step 2: Domain Configuration

### 2.1 Configure DNS Records
1. **Go to your domain registrar** (where you bought onlylands.in)
2. **Add these DNS records:**
   ```
   Type: A
   Name: @
   Value: [YOUR_DROPLET_IP]
   TTL: 300

   Type: A  
   Name: www
   Value: [YOUR_DROPLET_IP]
   TTL: 300

   Type: A
   Name: api
   Value: [YOUR_DROPLET_IP] 
   TTL: 300
   ```

3. **Wait 5-10 minutes** for DNS propagation

## Step 3: Server Setup

### 3.1 Connect to Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### 3.2 Initial Server Setup
```bash
# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y nginx nodejs npm python3 python3-pip git docker.io docker-compose ufw

# Install Node.js 18 (for React)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install yarn
npm install -g yarn

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Configure firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

### 3.3 Install MongoDB (if using Option B)
```bash
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
```

## Step 4: Application Deployment

### 4.1 Clone Your Repository
```bash
# Create app directory
mkdir -p /var/www/onlylands
cd /var/www/onlylands

# Option 1: If you have GitHub repo
git clone https://github.com/YOURUSERNAME/onlylands.git .

# Option 2: Upload your files manually
# Use scp or rsync to upload your app files
```

### 4.2 Set up Backend
```bash
cd /var/www/onlylands/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production environment file
cat > .env << EOF
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
```

### 4.3 Set up Frontend
```bash
cd /var/www/onlylands/frontend

# Install dependencies
yarn install

# Create production environment file
cat > .env << EOF
REACT_APP_BACKEND_URL=https://api.onlylands.in
EOF

# Build production version
yarn build
```

## Step 5: Configure Nginx

### 5.1 Create Nginx Configuration
```bash
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
}
EOF

# Enable the site
ln -s /etc/nginx/sites-available/onlylands /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t
systemctl reload nginx
```

## Step 6: Set up Process Management

### 6.1 Create Systemd Service for Backend
```bash
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

# Enable and start the service
systemctl enable onlylands-backend
systemctl start onlylands-backend
systemctl status onlylands-backend
```

## Step 7: SSL/HTTPS Setup with Let's Encrypt

### 7.1 Install Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 7.2 Get SSL Certificates
```bash
# Get certificates for all domains
certbot --nginx -d onlylands.in -d www.onlylands.in -d api.onlylands.in

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose whether to share email with EFF
# - Choose option 2 (redirect HTTP to HTTPS)
```

### 7.3 Set up Auto-renewal
```bash
# Test renewal
certbot renew --dry-run

# Set up cron job for auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## Step 8: Final Configuration

### 8.1 Update Frontend Environment for HTTPS
```bash
cd /var/www/onlylands/frontend

# Update .env for HTTPS
cat > .env << EOF
REACT_APP_BACKEND_URL=https://api.onlylands.in
EOF

# Rebuild
yarn build
```

### 8.2 Restart All Services
```bash
systemctl restart onlylands-backend
systemctl reload nginx
```

## Step 9: Monitoring and Maintenance

### 9.1 Set up Log Monitoring
```bash
# View backend logs
journalctl -u onlylands-backend -f

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 9.2 Set up Backup Script
```bash
cat > /root/backup-onlylands.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --out $BACKUP_DIR/mongo_$DATE

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /var/www/onlylands

# Keep only last 7 backups
find $BACKUP_DIR -name "mongo_*" -mtime +7 -delete
find $BACKUP_DIR -name "app_*" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup-onlylands.sh

# Schedule daily backups
echo "0 2 * * * /root/backup-onlylands.sh" | crontab -
```

## Step 10: Testing

### 10.1 Test Your Deployment
1. **Frontend:** Visit https://onlylands.in
2. **API:** Visit https://api.onlylands.in/docs
3. **Test complete flow:** Create account → Post listing → Upload image

### 10.2 Performance Optimization
```bash
# Install PM2 for better process management (optional)
npm install -g pm2

# Enable Nginx gzip compression
cat >> /etc/nginx/nginx.conf << 'EOF'
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
EOF

systemctl reload nginx
```

## Estimated Monthly Costs:
- **Droplet (2GB):** $18/month
- **Managed MongoDB:** $15/month  
- **Domain:** Already owned
- **SSL:** Free (Let's Encrypt)
- **Total:** ~$33/month

## Troubleshooting Common Issues:

1. **502 Bad Gateway:** Backend service not running
   ```bash
   systemctl restart onlylands-backend
   ```

2. **SSL Certificate Issues:**
   ```bash
   certbot renew --force-renewal
   ```

3. **MongoDB Connection Issues:**
   ```bash
   systemctl status mongod
   systemctl restart mongod
   ```

4. **File Upload Issues:** Check file permissions
   ```bash
   chown -R www-data:www-data /var/www/onlylands
   ```

## Next Steps After Deployment:

1. **Monitor Traffic:** Set up Google Analytics
2. **Set up Alerts:** Use DigitalOcean monitoring
3. **Scale:** Add load balancer when traffic grows
4. **Security:** Regular security updates
5. **Backup:** Test backup restoration

Your OnlyLands application will be live at https://onlylands.in! 🚀