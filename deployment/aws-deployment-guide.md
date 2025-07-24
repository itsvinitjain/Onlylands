# OnlyLands AWS Deployment Guide

## 🚀 Deploy OnlyLands on AWS with Custom Domain

### AWS Architecture
- **EC2**: Application server (t3.small)
- **Route 53**: DNS management for onlylands.in
- **CloudFront**: CDN for frontend
- **S3**: File storage (already configured)
- **DocumentDB/MongoDB Atlas**: Database
- **Application Load Balancer**: SSL termination
- **Certificate Manager**: Free SSL certificates

### Estimated Monthly Cost: $25-40

## Phase 1: AWS Infrastructure Setup

### 1.1 Create EC2 Instance
1. **Go to AWS Console** → EC2 → Launch Instance
2. **Configuration:**
   - **Name:** onlylands-production
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** t3.small (2 vCPU, 2GB RAM) - $16.79/month
   - **Key Pair:** Create new or use existing
   - **Security Group:** Create new with these rules:
     ```
     SSH (22): Your IP only
     HTTP (80): 0.0.0.0/0
     HTTPS (443): 0.0.0.0/0
     Custom (8001): 0.0.0.0/0 (for API)
     ```
   - **Storage:** 20GB gp3 (included in pricing)

3. **Launch Instance** and note the **Public IP**

### 1.2 Set up Route 53 for Domain
1. **Go to Route 53** → Hosted Zones → Create Hosted Zone
2. **Domain:** onlylands.in
3. **Copy the 4 nameservers** (NS records)
4. **Go to your domain registrar** and update nameservers to AWS
5. **Wait 24-48 hours** for nameserver propagation

### 1.3 Request SSL Certificate
1. **Go to Certificate Manager** → Request Certificate
2. **Domain names:**
   - onlylands.in
   - www.onlylands.in
   - api.onlylands.in
3. **Validation:** DNS validation
4. **Add CNAME records** to Route 53 as instructed
5. **Wait for validation** (5-30 minutes)

## Phase 2: Database Setup

### Option A: MongoDB Atlas (Recommended - $9/month)
1. **Go to MongoDB Atlas** → Create Account
2. **Create Cluster:**
   - **Provider:** AWS
   - **Region:** Same as your EC2 (us-east-1)
   - **Tier:** M0 Sandbox (Free) or M2 ($9/month)
3. **Database Access:** Create user
4. **Network Access:** Add your EC2 IP
5. **Copy connection string**

### Option B: AWS DocumentDB ($57/month - more expensive)
1. **Go to DocumentDB** → Create Cluster
2. **Instance Class:** db.t3.medium
3. **Number of instances:** 1
4. **VPC:** Default VPC
5. **Copy connection string**

**Recommendation:** Use MongoDB Atlas M2 tier for cost efficiency.

## Phase 3: Application Deployment

### 3.1 Connect to EC2 Instance
```bash
# Download your key pair and connect
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 3.2 Run Server Setup Script
```bash
# Switch to root
sudo su -

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y nginx nodejs npm python3 python3-pip python3-venv git curl wget awscli

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install yarn
npm install -g yarn

# Configure firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable

# Create application directory
mkdir -p /var/www/onlylands
cd /var/www/onlylands
```

### 3.3 Set up Application
```bash
# Create directory structure
mkdir -p backend frontend

# You'll upload your files here (we'll do this next)
```

## Phase 4: Load Balancer & SSL Setup

### 4.1 Create Application Load Balancer
1. **Go to EC2** → Load Balancers → Create Load Balancer
2. **Type:** Application Load Balancer
3. **Name:** onlylands-alb
4. **Scheme:** Internet-facing
5. **IP address type:** IPv4
6. **VPC:** Default VPC
7. **Availability Zones:** Select 2 zones
8. **Security Group:** Create new:
   ```
   HTTP (80): 0.0.0.0/0
   HTTPS (443): 0.0.0.0/0
   ```

### 4.2 Create Target Groups
**Frontend Target Group:**
1. **Name:** onlylands-frontend
2. **Protocol:** HTTP, Port: 80
3. **Target type:** Instance
4. **Health check path:** /
5. **Register your EC2 instance**

**Backend Target Group:**
1. **Name:** onlylands-backend  
2. **Protocol:** HTTP, Port: 8001
3. **Target type:** Instance
4. **Health check path:** /docs
5. **Register your EC2 instance**

### 4.3 Configure ALB Listeners
**HTTPS Listener (443):**
- **Default action:** Forward to onlylands-frontend
- **SSL certificate:** Select your ACM certificate
- **Add rule:** If path starts with `/api` → Forward to onlylands-backend

**HTTP Listener (80):**
- **Default action:** Redirect to HTTPS

### 4.4 Update Route 53 Records
1. **Go to Route 53** → Your hosted zone
2. **Create records:**
   ```
   Type: A (Alias)
   Name: @ (root domain)
   Value: Your ALB DNS name
   
   Type: A (Alias)  
   Name: www
   Value: Your ALB DNS name
   
   Type: A (Alias)
   Name: api  
   Value: Your ALB DNS name
   ```

## Phase 5: Application Configuration