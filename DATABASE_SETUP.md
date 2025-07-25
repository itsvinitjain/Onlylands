# OnlyLands Database Management Guide

## 🎯 Overview
This guide helps you set up third-party tools to manage and view your OnlyLands MongoDB database.

## 📊 Built-in Admin Panel
**Access**: Click the "Admin" button in the OnlyLands app navigation

**Features**:
- 📈 Dashboard with platform statistics
- 👥 Users management (sellers & brokers)
- 🏞️ Listings with photo/video counts
- 🏢 Brokers with contact tracking
- 💳 Payments and transaction history
- 📞 WhatsApp notification logs

**URL**: https://e1833c0e-8697-4c1d-82e1-ad61f5ff183e.preview.emergentagent.com

## 🔧 MongoDB Compass (Recommended)

### Download & Install
1. Visit: https://www.mongodb.com/products/compass
2. Download MongoDB Compass (Free)
3. Install on your local machine

### Connection Settings
```
Connection String: mongodb://localhost:27017
Database Name: onlylands_db
```

### Collections Available
- **users** - User accounts (sellers & brokers)
- **listings** - Land listings with photos/videos
- **brokers** - Broker profiles and contact info
- **payments** - Payment transactions and orders
- **notifications** - WhatsApp broadcast logs

### Features
- ✅ Visual query builder
- ✅ Data export/import
- ✅ Index management
- ✅ Real-time monitoring
- ✅ Aggregation pipeline builder

## 🌐 Alternative Web-Based Tools

### 1. MongoDB Atlas (Cloud)
- **URL**: https://cloud.mongodb.com
- Create free account
- Import your data to cloud
- Web-based management interface

### 2. Robo 3T (Free Desktop)
- **URL**: https://robomongo.org
- Lightweight MongoDB client
- Good for simple queries

### 3. Studio 3T (Professional)
- **URL**: https://studio3t.com
- Advanced MongoDB IDE
- Free trial, then paid

## 📱 Database Schema

### Users Collection
```json
{
  "user_id": "uuid",
  "phone": "+917021758061",
  "user_type": "seller|broker",
  "name": "string",
  "email": "string",
  "created_at": "datetime"
}
```

### Listings Collection
```json
{
  "listing_id": "uuid",
  "title": "string",
  "location": "string",
  "area": "string",
  "price": "string",
  "description": "string",
  "latitude": "float",
  "longitude": "float",
  "images": [
    {
      "filename": "string",
      "content_type": "string",
      "data": "base64_string"
    }
  ],
  "videos": [
    {
      "filename": "string", 
      "content_type": "string",
      "data": "base64_string"
    }
  ],
  "status": "active|pending_payment",
  "payment_status": "paid|pending",
  "broadcast_sent": "boolean",
  "created_at": "datetime"
}
```

### Brokers Collection
```json
{
  "broker_id": "uuid",
  "name": "string",
  "agency": "string",
  "phone": "whatsapp:+917021758061",
  "email": "string",
  "location": "string",
  "active": "boolean",
  "last_contacted": "datetime",
  "created_at": "datetime"
}
```

### Payments Collection
```json
{
  "payment_id": "uuid",
  "razorpay_order_id": "string",
  "razorpay_payment_id": "string",
  "listing_id": "uuid",
  "amount": 29900,
  "status": "paid|created",
  "created_at": "datetime",
  "paid_at": "datetime"
}
```

## 🚀 Quick Start with MongoDB Compass

1. **Install MongoDB Compass**
2. **Open Compass**
3. **New Connection**
4. **Enter**: `mongodb://localhost:27017`
5. **Connect**
6. **Select Database**: `onlylands_db`
7. **Browse Collections**: users, listings, brokers, payments, notifications

## 📈 Common Queries

### Find all active listings
```javascript
{ "status": "active" }
```

### Find listings with photos
```javascript
{ "images.0": { "$exists": true } }
```

### Find recent users (last 7 days)
```javascript
{ 
  "created_at": { 
    "$gte": new Date(Date.now() - 7*24*60*60*1000) 
  } 
}
```

### Find successful payments
```javascript
{ "status": "paid" }
```

## 🔐 Security Notes

- Database runs on localhost only
- No external connections allowed
- All API endpoints require proper authentication
- Sensitive data (images/videos) stored as base64
- Payment integration uses Razorpay test mode

## 📞 Support

For database-related issues:
1. Check the built-in Admin Panel first
2. Use MongoDB Compass for advanced queries
3. Check server logs: `tail -f /var/log/supervisor/backend.*.log`

---
**Generated for OnlyLands - Agricultural & Residential Land Marketplace**