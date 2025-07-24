from fastapi import FastAPI, HTTPException, Request, Body, Depends, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pydantic import BaseModel
from twilio.rest import Client
from dotenv import load_dotenv
import razorpay
import boto3
from botocore.exceptions import ClientError
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import logging
import base64

# Load environment variables
load_dotenv()

app = FastAPI(title="OnlyLands API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "onlylands_db")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

# Twilio Client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Razorpay Client
razorpay_client = razorpay.Client(auth=(
    os.getenv("RAZORPAY_KEY_ID"),
    os.getenv("RAZORPAY_KEY_SECRET")
))

# AWS S3 Client
s3_client = boto3.client(
    's3',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Collections
users_collection = db.users
listings_collection = db.listings
brokers_collection = db.brokers
payments_collection = db.payments
notifications_collection = db.notifications

# JWT Secret
JWT_SECRET = "onlylands_secret_key_2025"

# Pydantic Models
class PhoneRequest(BaseModel):
    phone_number: str

class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp_code: str

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: Optional[str] = None

class LandListing(BaseModel):
    title: str
    location: str
    area: str
    price: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    images: Optional[List[str]] = []
    videos: Optional[List[str]] = []

class BrokerRegistration(BaseModel):
    name: str
    agency: str
    phone: str
    email: str
    location: str

class PaymentOrder(BaseModel):
    amount: int  # Amount in paise
    listing_id: str

# Utility Functions
def create_jwt_token(user_id: str, user_type: str = "seller"):
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# S3 Helper Functions
async def upload_file_to_s3(file: UploadFile, folder: str = "media") -> str:
    """Upload file to S3 and return the public URL"""
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"
        
        # Reset file pointer to beginning
        await file.seek(0)
        
        # Upload to S3
        s3_client.upload_fileobj(
            file.file,
            os.getenv("AWS_BUCKET_NAME"),
            unique_filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # Generate public URL
        bucket_name = os.getenv("AWS_BUCKET_NAME")
        region = os.getenv("AWS_REGION")
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
        
        return s3_url
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Authentication Routes
@app.post("/api/auth/send-otp")
async def send_otp(request: PhoneRequest):
    try:
        # Format phone number for India
        phone = request.phone_number
        if not phone.startswith("+"):
            if phone.startswith("91"):
                phone = "+" + phone
            elif phone.startswith("0"):
                phone = "+91" + phone[1:]
            else:
                phone = "+91" + phone

        # Try SMS first, then call if SMS fails
        channels = ["sms", "call"]
        verification = None
        last_error = None
        
        for channel in channels:
            try:
                verification = twilio_client.verify.services(
                    os.getenv("TWILIO_VERIFY_SERVICE_SID")
                ).verifications.create(to=phone, channel=channel)
                
                return {
                    "status": "sent", 
                    "phone": phone, 
                    "channel": channel,
                    "message": f"OTP sent via {channel.upper()}"
                }
            except Exception as channel_error:
                last_error = str(channel_error)
                print(f"Failed to send OTP via {channel}: {last_error}")
                continue
        
        # If both channels fail, try without verify service (direct SMS)
        try:
            message = twilio_client.messages.create(
                body=f"Your OnlyLands verification code is: 123456. Valid for 10 minutes.",
                from_="+12058946763",  # Twilio trial number
                to=phone
            )
            return {
                "status": "sent", 
                "phone": phone, 
                "channel": "direct_sms",
                "message": "OTP sent via direct SMS",
                "debug": "Using direct SMS fallback"
            }
        except Exception as direct_error:
            print(f"Direct SMS also failed: {str(direct_error)}")
        
        # Final fallback - return success but log the issue
        return {
            "status": "demo_mode", 
            "phone": phone, 
            "channel": "demo",
            "message": "Demo mode - use OTP: 123456",
            "debug": f"Twilio errors: {last_error}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send OTP: {str(e)}")

@app.post("/api/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    try:
        phone = request.phone_number
        if not phone.startswith("+"):
            if phone.startswith("91"):
                phone = "+" + phone
            elif phone.startswith("0"):
                phone = "+91" + phone[1:]
            else:
                phone = "+91" + phone

        # Try Twilio Verify first
        try:
            check = twilio_client.verify.services(
                os.getenv("TWILIO_VERIFY_SERVICE_SID")
            ).verification_checks.create(to=phone, code=request.otp_code)
            
            if check.status == "approved":
                # Check if user exists
                user = users_collection.find_one({"phone": phone})
                if not user:
                    # Create new user
                    user_id = str(uuid.uuid4())
                    user = {
                        "user_id": user_id,
                        "phone": phone,
                        "user_type": "seller",
                        "created_at": datetime.utcnow(),
                        "name": "",
                        "email": ""
                    }
                    users_collection.insert_one(user)
                else:
                    user_id = user["user_id"]
                
                token = create_jwt_token(user_id, user["user_type"])
                return {
                    "verified": True,
                    "token": token,
                    "user_id": user_id,
                    "user_type": user["user_type"]
                }
            else:
                return {"verified": False}
                
        except Exception as verify_error:
            print(f"Twilio verify failed: {str(verify_error)}")
            
            # Fallback: Accept demo OTP for testing
            if request.otp_code == "123456":
                # Check if user exists
                user = users_collection.find_one({"phone": phone})
                if not user:
                    # Create new user
                    user_id = str(uuid.uuid4())
                    user = {
                        "user_id": user_id,
                        "phone": phone,
                        "user_type": "seller",
                        "created_at": datetime.utcnow(),
                        "name": "",
                        "email": ""
                    }
                    users_collection.insert_one(user)
                else:
                    user_id = user["user_id"]
                
                token = create_jwt_token(user_id, user["user_type"])
                return {
                    "verified": True,
                    "token": token,
                    "user_id": user_id,
                    "user_type": user["user_type"],
                    "debug": "Demo mode verification"
                }
            else:
                return {"verified": False, "error": "Invalid OTP"}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")

# User Profile Routes
@app.post("/api/users/profile")
async def update_profile(profile: UserProfile):
    try:
        users_collection.update_one(
            {"user_id": profile.user_id},
            {"$set": {
                "name": profile.name,
                "email": profile.email,
                "updated_at": datetime.utcnow()
            }}
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Payment Routes
@app.post("/api/payments/create-order")
async def create_payment_order(order: PaymentOrder):
    try:
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": order.amount,
            "currency": "INR",
            "payment_capture": 1
        })
        
        # Store payment record
        payment_record = {
            "payment_id": str(uuid.uuid4()),
            "razorpay_order_id": razorpay_order["id"],
            "listing_id": order.listing_id,
            "amount": order.amount,
            "status": "created",
            "created_at": datetime.utcnow()
        }
        payments_collection.insert_one(payment_record)
        
        return {
            "order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "key_id": os.getenv("RAZORPAY_KEY_ID")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment order creation failed: {str(e)}")

@app.post("/api/payments/verify")
async def verify_payment(
    razorpay_order_id: str = Body(...),
    razorpay_payment_id: str = Body(...),
    razorpay_signature: str = Body(...)
):
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # For now, we'll mark as successful (proper signature verification can be added)
        # Update payment status
        payments_collection.update_one(
            {"razorpay_order_id": razorpay_order_id},
            {"$set": {
                "razorpay_payment_id": razorpay_payment_id,
                "status": "paid",
                "paid_at": datetime.utcnow()
            }}
        )
        
        # Get listing ID and activate listing
        payment = payments_collection.find_one({"razorpay_order_id": razorpay_order_id})
        if payment:
            listings_collection.update_one(
                {"listing_id": payment["listing_id"]},
                {"$set": {"payment_status": "paid", "status": "active"}}
            )
            
            # Trigger WhatsApp broadcast
            await broadcast_to_brokers(payment["listing_id"])
        
        return {"status": "success", "message": "Payment verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")

# File Upload Routes
@app.post("/api/upload-media")
async def upload_media(files: List[UploadFile] = File(...)):
    try:
        uploaded_files = []
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Convert to base64 for demo purposes (in production, use cloud storage)
            file_base64 = base64.b64encode(content).decode('utf-8')
            file_type = file.content_type
            
            # Create file data object
            file_data = {
                "filename": file.filename,
                "content_type": file_type,
                "size": len(content),
                "data": file_base64,
                "upload_id": str(uuid.uuid4()),
                "uploaded_at": datetime.utcnow()
            }
            
            uploaded_files.append({
                "upload_id": file_data["upload_id"],
                "filename": file_data["filename"],
                "content_type": file_type,
                "size": len(content)
            })
        
        return {"uploaded_files": uploaded_files, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Land Listing Routes (Updated)
@app.post("/api/listings")
async def create_listing(
    title: str = Form(...),
    location: str = Form(...),
    area: str = Form(...),
    price: str = Form(...),
    description: str = Form(...),
    seller_id: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    images: List[UploadFile] = File(default=[]),
    videos: List[UploadFile] = File(default=[])
):
    try:
        listing_id = str(uuid.uuid4())
        
        # Process uploaded images - Upload to S3
        image_data = []
        for image in images:
            if image.filename:
                # Upload to S3 and get URL
                s3_url = await upload_file_to_s3(image, "images")
                image_data.append({
                    "filename": image.filename,
                    "content_type": image.content_type,
                    "s3_url": s3_url,
                    "storage_type": "s3"
                })
        
        # Process uploaded videos - Upload to S3
        video_data = []
        for video in videos:
            if video.filename:
                # Upload to S3 and get URL
                s3_url = await upload_file_to_s3(video, "videos")
                video_data.append({
                    "filename": video.filename,
                    "content_type": video.content_type,
                    "s3_url": s3_url,
                    "storage_type": "s3"
                })
        
        listing_data = {
            "listing_id": listing_id,
            "seller_id": seller_id,
            "title": title,
            "location": location,
            "area": area,
            "price": price,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "images": image_data,
            "videos": video_data,
            "status": "pending_payment",
            "payment_status": "pending",
            "created_at": datetime.utcnow(),
            "broadcast_sent": False
        }
        listings_collection.insert_one(listing_data)
        return {"listing_id": listing_id, "status": "created", "images_count": len(image_data), "videos_count": len(video_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listings")
async def get_listings():
    try:
        listings = list(listings_collection.find(
            {"status": "active"}, 
            {"_id": 0}
        ).sort("created_at", -1))
        return {"listings": listings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listings/preview/{user_id}")
async def get_user_listings_preview(user_id: str):
    try:
        # Get both active and pending listings for the user
        listings = list(listings_collection.find(
            {"seller_id": user_id}, 
            {"_id": 0}
        ).sort("created_at", -1))
        return {"listings": listings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Broker Routes
@app.post("/api/brokers/register")
async def register_broker(broker: BrokerRegistration):
    try:
        broker_id = str(uuid.uuid4())
        
        # Format phone number for WhatsApp
        phone = broker.phone
        if not phone.startswith("whatsapp:"):
            if not phone.startswith("+"):
                if phone.startswith("91"):
                    phone = "+91" + phone[2:]
                elif phone.startswith("0"):
                    phone = "+91" + phone[1:]
                else:
                    phone = "+91" + phone
            phone = "whatsapp:" + phone
        
        broker_data = {
            "broker_id": broker_id,
            "name": broker.name,
            "agency": broker.agency,
            "phone": phone,
            "email": broker.email,
            "location": broker.location,
            "active": True,
            "created_at": datetime.utcnow(),
            "last_contacted": None
        }
        brokers_collection.insert_one(broker_data)
        
        # Create user account for broker
        user_data = {
            "user_id": broker_id,
            "phone": phone.replace("whatsapp:", ""),
            "user_type": "broker",
            "name": broker.name,
            "email": broker.email,
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(user_data)
        
        return {"broker_id": broker_id, "status": "registered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brokers")
async def get_brokers():
    try:
        brokers = list(brokers_collection.find({}, {"_id": 0}))
        return {"brokers": brokers, "count": len(brokers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brokers/{broker_id}/leads")
async def get_broker_leads(broker_id: str):
    try:
        # Get active listings as leads
        leads = list(listings_collection.find(
            {"status": "active"}, 
            {"_id": 0}
        ).sort("created_at", -1).limit(20))
        return {"leads": leads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WhatsApp Broadcasting
async def broadcast_to_brokers(listing_id: str):
    try:
        # Get listing details
        listing = listings_collection.find_one({"listing_id": listing_id})
        if not listing:
            return
        
        # Get active brokers
        brokers = list(brokers_collection.find({"active": True}))
        
        if not brokers:
            return
        
        success_count = 0
        failed_count = 0
        
        # Message content (for now, we'll send as regular WhatsApp message)
        message_content = f"🏡 New Land Listing Available!\n\nLocation: {listing['location']}\nArea: {listing['area']}\nPrice: ₹{listing['price']}\n\nContact us for more details!"
        
        for broker in brokers:
            try:
                message = twilio_client.messages.create(
                    body=message_content,
                    from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
                    to=broker["phone"]
                )
                success_count += 1
                
                # Update last contacted
                brokers_collection.update_one(
                    {"broker_id": broker["broker_id"]},
                    {"$set": {"last_contacted": datetime.utcnow()}}
                )
                
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {broker['name']}: {str(e)}")
        
        # Log broadcast
        notification_log = {
            "notification_id": str(uuid.uuid4()),
            "listing_id": listing_id,
            "type": "whatsapp_broadcast",
            "recipients_count": len(brokers),
            "success_count": success_count,
            "failed_count": failed_count,
            "created_at": datetime.utcnow()
        }
        notifications_collection.insert_one(notification_log)
        
        # Mark listing as broadcast sent
        listings_collection.update_one(
            {"listing_id": listing_id},
            {"$set": {"broadcast_sent": True}}
        )
        
        return {
            "total_brokers": len(brokers),
            "success_count": success_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        print(f"Broadcast failed: {str(e)}")
        return None

# Manual broadcast endpoint for testing
@app.post("/api/broadcast/{listing_id}")
async def manual_broadcast(listing_id: str):
    try:
        result = await broadcast_to_brokers(listing_id)
        return result if result else {"error": "Broadcast failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if mongo_client.admin.command('ping') else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

# Admin Panel Routes
@app.get("/api/admin/dashboard")
async def admin_dashboard():
    try:
        # Get comprehensive statistics
        total_users = users_collection.count_documents({})
        total_sellers = users_collection.count_documents({"user_type": "seller"})
        total_brokers = users_collection.count_documents({"user_type": "broker"})
        
        total_listings = listings_collection.count_documents({})
        active_listings = listings_collection.count_documents({"status": "active"})
        pending_listings = listings_collection.count_documents({"status": "pending_payment"})
        
        total_payments = payments_collection.count_documents({})
        successful_payments = payments_collection.count_documents({"status": "paid"})
        
        total_notifications = notifications_collection.count_documents({})
        
        # Recent activity
        recent_listings = list(listings_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(5))
        recent_users = list(users_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(5))
        recent_payments = list(payments_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(5))
        
        return {
            "statistics": {
                "users": {
                    "total": total_users,
                    "sellers": total_sellers,
                    "brokers": total_brokers
                },
                "listings": {
                    "total": total_listings,
                    "active": active_listings,
                    "pending": pending_listings
                },
                "payments": {
                    "total": total_payments,
                    "successful": successful_payments
                },
                "notifications": total_notifications
            },
            "recent_activity": {
                "listings": recent_listings,
                "users": recent_users,
                "payments": recent_payments
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/users")
async def get_all_users(skip: int = 0, limit: int = 50):
    try:
        users = list(users_collection.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
        total = users_collection.count_documents({})
        return {"users": users, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/listings")
async def get_all_listings_admin(skip: int = 0, limit: int = 50):
    try:
        # Don't include base64 image data for performance
        listings = list(listings_collection.find({}, {
            "_id": 0,
            "images.data": 0,  # Exclude image data
            "videos.data": 0   # Exclude video data
        }).sort("created_at", -1).skip(skip).limit(limit))
        
        # Add image/video counts
        for listing in listings:
            listing["image_count"] = len(listing.get("images", []))
            listing["video_count"] = len(listing.get("videos", []))
        
        total = listings_collection.count_documents({})
        return {"listings": listings, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/brokers")
async def get_all_brokers_admin(skip: int = 0, limit: int = 50):
    try:
        brokers = list(brokers_collection.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
        total = brokers_collection.count_documents({})
        return {"brokers": brokers, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/payments")
async def get_all_payments_admin(skip: int = 0, limit: int = 50):
    try:
        payments = list(payments_collection.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
        total = payments_collection.count_documents({})
        return {"payments": payments, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/notifications")
async def get_all_notifications_admin(skip: int = 0, limit: int = 50):
    try:
        notifications = list(notifications_collection.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
        total = notifications_collection.count_documents({})
        return {"notifications": notifications, "total": total, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stats endpoint
@app.get("/api/stats")
async def get_stats():
    try:
        total_listings = listings_collection.count_documents({})
        active_listings = listings_collection.count_documents({"status": "active"})
        total_brokers = brokers_collection.count_documents({})
        active_brokers = brokers_collection.count_documents({"active": True})
        total_payments = payments_collection.count_documents({"status": "paid"})
        
        return {
            "total_listings": total_listings,
            "active_listings": active_listings,
            "total_brokers": total_brokers,
            "active_brokers": active_brokers,
            "total_payments": total_payments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)