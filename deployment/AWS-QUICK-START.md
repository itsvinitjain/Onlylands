# OnlyLands AWS Deployment - Quick Start Guide

## 🚀 Deploy to AWS in 45 Minutes

### Total Cost: ~$25-40/month
- EC2 t3.small: $16.79/month
- MongoDB Atlas M2: $9/month  
- Route 53: $0.50/month
- Application Load Balancer: $16.20/month
- SSL Certificate: Free
- S3 Storage: ~$1-5/month

---

## Phase 1: AWS Infrastructure (15 minutes)

### Step 1: Create EC2 Instance
1. **AWS Console** → EC2 → Launch Instance
2. **Settings:**
   ```
   Name: onlylands-production
   AMI: Ubuntu Server 22.04 LTS
   Instance Type: t3.small (2 vCPU, 2GB RAM)
   Key Pair: Create new or use existing
   Security Group: Create new
   ```

3. **Security Group Rules:**
   ```
   SSH (22): Your IP only
   HTTP (80): 0.0.0.0/0
   HTTPS (443): 0.0.0.0/0  
   Custom (8001): 0.0.0.0/0
   ```

4. **Launch & Note Public IP**

### Step 2: Set up MongoDB Atlas
1. **Go to MongoDB Atlas** → Create Free Account
2. **Create Cluster:**
   - Provider: AWS
   - Region: us-east-1 (same as EC2)
   - Tier: M0 (Free) or M2 ($9/month recommended)
3. **Database Access:** Create user (save username/password)
4. **Network Access:** Add 0.0.0.0/0 (we'll restrict later)
5. **Copy connection string** for later

### Step 3: Request SSL Certificate
1. **AWS Console** → Certificate Manager
2. **Request Certificate:**
   ```
   Domain names:
   - onlylands.in
   - www.onlylands.in  
   - api.onlylands.in
   ```
3. **Validation:** DNS validation
4. **Keep the tab open** - we'll add DNS records later

---

## Phase 2: Server Setup (10 minutes)

### Step 1: Connect to EC2
```bash
# Download your key pair and connect
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Switch to root
sudo su -
```

### Step 2: Run Server Setup
```bash
# Download and run setup script
curl -sSL https://raw.githubusercontent.com/yourusername/onlylands/main/deployment/aws-setup-server.sh | bash

# Or upload the script manually:
# Upload aws-setup-server.sh to /root/
chmod +x /root/aws-setup-server.sh
/root/aws-setup-server.sh
```

---

## Phase 3: Application Deployment (10 minutes)

### Step 1: Upload Application Files

**Method A: Using SCP (Recommended)**
```bash
# From your local machine
tar --exclude="node_modules" --exclude="__pycache__" -czf onlylands-app.tar.gz backend/ frontend/

# Upload to server
scp -i your-key.pem onlylands-app.tar.gz ubuntu@YOUR_EC2_IP:/tmp/

# On server, extract files
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
sudo su -
cd /var/www/onlylands
tar -xzf /tmp/onlylands-app.tar.gz
chown -R www-data:www-data /var/www/onlylands
```

### Step 2: Configure MongoDB Connection
```bash
# Edit backend environment
nano /var/www/onlylands/backend/.env

# Update MONGO_URL with your Atlas connection string:
MONGO_URL="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/onlylands_db?retryWrites=true&w=majority"
```

### Step 3: Deploy Application
```bash
# Run deployment script
/root/aws-deploy-app.sh
```

---

## Phase 4: Load Balancer & DNS (10 minutes)

### Step 1: Create Application Load Balancer
1. **EC2** → Load Balancers → Create Load Balancer
2. **Application Load Balancer:**
   ```
   Name: onlylands-alb
   Scheme: Internet-facing
   IP address type: IPv4
   VPC: Default VPC
   Subnets: Select 2+ availability zones
   Security Group: Create new (HTTP 80, HTTPS 443)
   ```

### Step 2: Create Target Groups

**Frontend Target Group:**
```
Name: onlylands-frontend-tg
Protocol: HTTP, Port: 80
Target type: Instance
Health check path: /health
Register targets: Your EC2 instance
```

**Backend Target Group:**
```
Name: onlylands-backend-tg  
Protocol: HTTP, Port: 8001
Target type: Instance
Health check path: /health
Register targets: Your EC2 instance
```

### Step 3: Configure ALB Listeners

**HTTPS Listener (443):**
- Default action: Forward to frontend target group
- SSL certificate: Select your ACM certificate
- Add rule: If path starts with `/api/*` → Forward to backend target group

**HTTP Listener (80):**
- Default action: Redirect to HTTPS

### Step 4: Set up Route 53
1. **Route 53** → Hosted Zones → Create Hosted Zone
2. **Domain:** onlylands.in
3. **Copy nameservers** and update at your domain registrar
4. **Create records:**
   ```
   Type: A (Alias)
   Name: @ (root)
   Value: Your ALB DNS name
   
   Type: A (Alias)
   Name: www
   Value: Your ALB DNS name
   
   Type: A (Alias)  
   Name: api
   Value: Your ALB DNS name
   ```

### Step 5: Validate SSL Certificate
1. **Go back to Certificate Manager**
2. **Add the CNAME records** shown in validation to Route 53
3. **Wait 5-30 minutes** for validation

---

## Phase 5: Final Testing (5 minutes)

### Test Your Deployment
```bash
# Check server status
/root/check-status.sh

# Test URLs (wait for DNS propagation)
curl -I https://onlylands.in
curl -I https://api.onlylands.in/docs
```

### Complete Application Test
1. **Visit:** https://onlylands.in
2. **Login:** +917021758061, OTP: 123456
3. **Post Land:** Add details, upload image
4. **Complete Payment:** Demo payment flow
5. **Verify:** Image displays correctly

---

## 🔧 AWS Management Commands

### Server Management
```bash
# Check all services
/root/check-status.sh

# View backend logs
pm2 logs onlylands-backend

# Restart backend
pm2 restart onlylands-backend

# Reload Nginx
systemctl reload nginx

# Update application
# 1. Upload new files
# 2. Run: /root/aws-deploy-app.sh
```

### AWS Console Monitoring
- **EC2:** Monitor instance health, CPU, memory
- **Load Balancer:** Check target health, traffic
- **Route 53:** Monitor DNS queries
- **CloudWatch:** Set up alarms for errors

---

## 🚨 Troubleshooting

### Backend Issues
```bash
# Check backend status
pm2 describe onlylands-backend

# View error logs
pm2 logs onlylands-backend --err

# Restart with logs
pm2 restart onlylands-backend && pm2 logs onlylands-backend
```

### Database Connection Issues
```bash
# Test MongoDB connection
cd /var/www/onlylands/backend
source venv/bin/activate
python3 -c "from pymongo import MongoClient; print('DB connected:', MongoClient('YOUR_MONGO_URL').admin.command('ping'))"
```

### Load Balancer Health Checks
```bash
# Test health endpoints
curl http://YOUR_EC2_IP/health
curl http://YOUR_EC2_IP:8001/health

# Check target group health in AWS Console
```

### SSL Certificate Issues
- Check ACM certificate status
- Verify DNS records in Route 53
- Wait up to 72 hours for DNS propagation

---

## 📊 Monitoring & Maintenance

### Daily Checks
```bash
# System health
/root/check-status.sh

# Application logs
pm2 logs onlylands-backend --lines 50

# Disk space
df -h
```

### Weekly Maintenance
```bash
# Update system
apt update && apt upgrade -y

# Restart services
pm2 restart all
systemctl restart nginx

# Check security
ufw status
```

### Backup Strategy
```bash
# MongoDB backup (Atlas auto-backups available)
# Application code backup
tar -czf /root/onlylands-backup-$(date +%Y%m%d).tar.gz /var/www/onlylands

# Upload to S3
aws s3 cp /root/onlylands-backup-*.tar.gz s3://onlyland/backups/
```

---

## 🎯 Go-Live Checklist

- [ ] EC2 instance running
- [ ] MongoDB Atlas cluster configured
- [ ] Application deployed and running
- [ ] Load Balancer created with target groups
- [ ] Route 53 hosted zone configured
- [ ] SSL certificate validated
- [ ] DNS records pointing to ALB
- [ ] Complete user flow tested
- [ ] Monitoring set up

---

## 🆘 Emergency Recovery

### If Everything Goes Down
```bash
# 1. Check EC2 instance status
# 2. Restart all services
pm2 restart all
systemctl restart nginx

# 3. Check Load Balancer target health
# 4. Verify DNS records

# 5. If still down, launch new EC2 instance:
# - Use same AMI or Ubuntu 22.04
# - Run setup scripts
# - Update target groups
```

### Quick Restore from Backup
```bash
# Download backup from S3
aws s3 cp s3://onlyland/backups/latest-backup.tar.gz /root/

# Extract and restore
cd /
tar -xzf /root/latest-backup.tar.gz
/root/aws-deploy-app.sh
```

---

**🎉 Your OnlyLands app will be live at https://onlylands.in**

**Total Setup Time:** ~45 minutes  
**Monthly Cost:** $25-40  
**Scalability:** Production-ready for thousands of users