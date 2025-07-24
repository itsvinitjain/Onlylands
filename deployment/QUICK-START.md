# OnlyLands DigitalOcean Deployment - Quick Start Guide

## 🚀 Deploy OnlyLands to DigitalOcean in 30 Minutes

### Phase 1: Create DigitalOcean Infrastructure (10 minutes)

#### 1.1 Create Droplet
1. **Login to DigitalOcean** → Create → Droplets
2. **Image:** Ubuntu 22.04 LTS
3. **Size:** $18/month (2 vCPU, 2GB RAM, 60GB SSD)
4. **Region:** Closest to India (Bangalore)
5. **Authentication:** Add your SSH key
6. **Hostname:** onlylands-prod
7. **Click Create** → Note down the IP address

#### 1.2 Initial Server Setup
```bash
# Connect to your server
ssh root@YOUR_DROPLET_IP

# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/your-repo/onlylands/main/deployment/setup-server.sh | bash

# Or if you have the files locally:
wget https://your-server.com/setup-server.sh
chmod +x setup-server.sh
./setup-server.sh
```

### Phase 2: Configure Domain (5 minutes)

#### 2.1 DNS Configuration
Go to your domain registrar and add these records:

```
Type: A    Name: @      Value: YOUR_DROPLET_IP    TTL: 300
Type: A    Name: www    Value: YOUR_DROPLET_IP    TTL: 300  
Type: A    Name: api    Value: YOUR_DROPLET_IP    TTL: 300
```

#### 2.2 Verify DNS (wait 5-10 minutes)
```bash
# Check if DNS is working
dig onlylands.in
dig www.onlylands.in
dig api.onlylands.in
```

### Phase 3: Deploy Application (10 minutes)

#### 3.1 Upload Application Files

**Method 1: Using Upload Script (Recommended)**
```bash
# On your local machine, edit the upload script
nano deployment/upload-to-server.sh

# Update SERVER_IP with your droplet IP
SERVER_IP="YOUR_DROPLET_IP"

# Run the upload script
chmod +x deployment/upload-to-server.sh
./deployment/upload-to-server.sh
```

**Method 2: Manual Upload**
```bash
# Upload files manually
scp -r backend/ root@YOUR_DROPLET_IP:/var/www/onlylands/
scp -r frontend/ root@YOUR_DROPLET_IP:/var/www/onlylands/
scp deployment/deploy-app.sh root@YOUR_DROPLET_IP:/root/

# Connect and deploy
ssh root@YOUR_DROPLET_IP
chmod +x /root/deploy-app.sh
/root/deploy-app.sh
```

#### 3.2 SSL Certificate Setup
```bash
# On the server, once DNS is ready
certbot --nginx -d onlylands.in -d www.onlylands.in -d api.onlylands.in

# Follow prompts:
# - Enter email: your-email@domain.com
# - Agree to terms: Y
# - Share email with EFF: Y/N (your choice)
# - Redirect HTTP to HTTPS: 2 (Yes)
```

### Phase 4: Verification (5 minutes)

#### 4.1 Test Your Deployment
```bash
# Check all services
/root/check-onlylands.sh

# Test URLs
curl -I https://onlylands.in
curl -I https://api.onlylands.in/docs
```

#### 4.2 Complete Flow Test
1. **Visit:** https://onlylands.in
2. **Login as Seller:** Use +917021758061, OTP: 123456
3. **Post Land:** Add title, location, upload image
4. **Complete Payment:** Demo payment flow
5. **Verify:** Check if listing appears with image

## 🔧 Management Commands

### Daily Operations
```bash
# Check system status
/root/check-onlylands.sh

# View live logs
journalctl -u onlylands-backend -f

# Restart services
systemctl restart onlylands-backend
systemctl reload nginx

# Backup data
/root/backup-onlylands.sh
```

### Troubleshooting
```bash
# If backend not working
systemctl status onlylands-backend
journalctl -u onlylands-backend --no-pager -n 20

# If frontend not loading
nginx -t
systemctl status nginx
tail -f /var/log/nginx/error.log

# If MongoDB issues
systemctl status mongod
tail -f /var/log/mongodb/mongod.log

# If SSL issues
certbot renew --dry-run
systemctl reload nginx
```

## 📊 Monitoring Setup

### 1. DigitalOcean Monitoring
1. **Droplet Dashboard** → Monitoring → Enable
2. **Set up alerts** for CPU, memory, disk usage
3. **Enable backups** (additional $3.60/month)

### 2. Application Monitoring
```bash
# Install htop for system monitoring
apt install htop

# Monitor in real-time
htop

# Check disk usage
df -h

# Check memory usage
free -h

# Monitor network connections
ss -tlnp
```

## 🔒 Security Hardening

### 1. Basic Security
```bash
# Update system regularly
apt update && apt upgrade -y

# Configure automatic security updates
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Disable root SSH (after setting up a user)
adduser admin
usermod -aG sudo admin
# Then edit /etc/ssh/sshd_config: PermitRootLogin no
```

### 2. Firewall Rules
```bash
# Check current rules
ufw status

# Add specific rules if needed
ufw allow from YOUR_OFFICE_IP to any port 22
ufw deny 22  # Disable SSH from everywhere else
```

## 💰 Cost Breakdown

| Service | Monthly Cost |
|---------|-------------|
| DigitalOcean Droplet (2GB) | $18 |
| Domain (onlylands.in) | $0 (already owned) |
| SSL Certificate | $0 (Let's Encrypt) |
| **Total** | **$18/month** |

**Optional Add-ons:**
- Droplet Backups: +$3.60/month
- Load Balancer (for scaling): +$12/month
- Managed MongoDB: +$15/month

## 🚀 Scaling Plan

### When to Scale (Traffic Indicators)
- **CPU usage > 80%** consistently
- **Memory usage > 90%**
- **Response time > 2 seconds**
- **500+ concurrent users**

### Scaling Options
1. **Vertical Scaling:** Resize droplet to 4GB RAM ($36/month)
2. **Horizontal Scaling:** Add load balancer + multiple droplets
3. **Database Scaling:** Move to managed MongoDB Atlas
4. **CDN:** Add CloudFlare for global performance

## 📈 Performance Optimization

### 1. Frontend Optimization
```bash
# Enable Nginx compression
nano /etc/nginx/nginx.conf
# Add gzip settings (already included in setup script)

# Cache static files
# Already configured in Nginx config
```

### 2. Backend Optimization
```bash
# Use Gunicorn for production (alternative to uvicorn)
pip install gunicorn
# Update systemd service to use: gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app
```

### 3. Database Optimization
```bash
# MongoDB index optimization
mongo onlylands_db
db.listings.createIndex({"status": 1, "created_at": -1})
db.users.createIndex({"phone": 1})
```

## 🎯 Go-Live Checklist

- [ ] Droplet created and configured
- [ ] DNS records configured for onlylands.in
- [ ] Application files uploaded
- [ ] SSL certificates installed
- [ ] All services running
- [ ] Complete user flow tested
- [ ] Backup script scheduled
- [ ] Monitoring alerts set up
- [ ] Performance optimized

## 🆘 Emergency Contacts & Resources

### Support Channels
- **DigitalOcean Support:** Available 24/7 via ticket
- **Community:** DigitalOcean Community tutorials
- **Documentation:** [OnlyLands Docs](deployment-docs)

### Quick Recovery
```bash
# If everything breaks, restore from backup
/root/backup-onlylands.sh
# Then restore MongoDB from /root/backups/
```

---

**🎉 Congratulations!** Your OnlyLands application is now live at **https://onlylands.in**

**Total Setup Time:** ~30 minutes  
**Monthly Cost:** $18  
**Scalability:** Ready for 1000+ users