# OnlyLands Simple AWS Deployment Guide

## 🚀 Deploy to AWS EC2 (Simple Setup) - $17-26/month

### Your Configuration:
- **Server:** AWS EC2 in Mumbai (ap-south-1)
- **IP:** 51.21.198.121
- **Domain:** onlylands.in (GoDaddy)
- **Database:** MongoDB Atlas

---

## Step 1: Connect to Your Server

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@51.21.198.121

# Switch to root
sudo su -
```

## Step 2: Server Setup

```bash
# Download and run setup script
wget https://raw.githubusercontent.com/yourusername/onlylands/main/deployment/aws-simple-setup.sh
chmod +x aws-simple-setup.sh
./aws-simple-setup.sh
```

## Step 3: Upload Your Application

```bash
# From your local machine, upload the files
scp -i your-key.pem -r backend/ ubuntu@51.21.198.121:/tmp/
scp -i your-key.pem -r frontend/ ubuntu@51.21.198.121:/tmp/

# On server, move files
ssh -i your-key.pem ubuntu@51.21.198.121
sudo su -
mv /tmp/backend/* /var/www/onlylands/backend/
mv /tmp/frontend/* /var/www/onlylands/frontend/
chown -R www-data:www-data /var/www/onlylands/
```

## Step 4: Configure Credentials

You need to add your API credentials to the application. Update these files:

### 4.1 Backend Environment
```bash
nano /var/www/onlylands/backend/.env
```

Replace the placeholder values with your actual credentials:
- MongoDB Atlas connection string  
- Twilio credentials (OTP & WhatsApp)
- Razorpay credentials (Payments)
- AWS S3 credentials (File storage)

### 4.2 AWS CLI Credentials
```bash
nano /root/.aws/credentials
```

Add your AWS credentials for S3 access.

## Step 5: Deploy Application

```bash
# Run deployment script
/root/aws-simple-deploy.sh
```

## Step 6: Configure GoDaddy DNS

Add these DNS records in GoDaddy:

```
Type: A    Name: @      Value: 51.21.198.121    TTL: 600
Type: A    Name: www    Value: 51.21.198.121    TTL: 600  
Type: A    Name: api    Value: 51.21.198.121    TTL: 600
```

## Step 7: SSL Certificate Setup

Wait 5-10 minutes for DNS propagation, then:

```bash
# Set up SSL certificates
/root/setup-ssl.sh
```

## Step 8: Final Testing

```bash
# Check all services
/root/check-status.sh

# Test your application
curl -I https://onlylands.in
curl -I https://api.onlylands.in/docs
```

---

## 🔧 Management Commands

```bash
# Check status
/root/check-status.sh

# View backend logs
pm2 logs onlylands-backend

# Restart backend
pm2 restart onlylands-backend

# Edit credentials
nano /var/www/onlylands/backend/.env
```

---

## 💰 Monthly Costs:
- EC2 t3.small: $16.79/month
- MongoDB Atlas M2: $9/month
- **Total: ~$26/month** (or $17 with free M0 tier)

---

## 🎯 Your Final URLs:
- **Website:** https://onlylands.in
- **API:** https://api.onlylands.in/docs  
- **Admin:** https://onlylands.in (admin button in app)

## 🆘 Need Help?
- Check logs: `pm2 logs onlylands-backend`
- Restart services: `pm2 restart all && systemctl reload nginx`
- Check server status: `/root/check-status.sh`