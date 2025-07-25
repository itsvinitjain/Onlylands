from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import jwt
import hashlib
from datetime import datetime, timedelta
import uuid
import boto3
from botocore.exceptions import ClientError
import pymongo
from pymongo import MongoClient
import razorpay
from twilio.rest import Client
import json
import base64

# Initialize FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'onlylands')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_VERIFY_SERVICE_SID = os.environ.get('TWILIO_VERIFY_SERVICE_SID')

# Razorpay configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_REGION = os.environ.get('S3_REGION', 'us-east-1')

# Initialize services
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
security = HTTPBearer()

# Initialize Twilio
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    twilio_client = None

# Initialize Razorpay
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

# Initialize AWS S3
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=S3_REGION
    )
else:
    s3_client = None

# Pydantic models
class OTPRequest(BaseModel):
    phone_number: str

class OTPVerify(BaseModel):
    phone_number: str
    otp: str

class BrokerSignup(BaseModel):
    name: str
    agency: str
    phone_number: str
    email: str
    photo: Optional[str] = None

class PaymentRequest(BaseModel):
    amount: int
    currency: str = "INR"
    listing_id: str

class AdminLogin(BaseModel):
    username: str
    password: str

# Helper functions
def get_image_src(image_data):
    """Helper function to handle both base64 and S3 URLs"""
    if image_data and image_data.startswith('data:'):
        return image_data
    elif image_data and image_data.startswith('https://'):
        return image_data
    else:
        return None

def upload_to_s3(file_content, filename, content_type):
    """Upload file to S3 and return URL"""
    if not s3_client:
        return None
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType=content_type
        )
        return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{filename}"
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return None

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token for regular users"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token for admin users"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_type = payload.get("user_type")
        if user_type != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.get("/api/")
async def root():
    return {"message": "OnlyLands API is running"}

@app.post("/api/send-otp")
async def send_otp(request: dict):
    """Send OTP to phone number using Twilio"""
    try:
        phone_number = request.get("phone_number")
        user_type = request.get("user_type", "seller")
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        if not twilio_client or not TWILIO_VERIFY_SERVICE_SID:
            raise HTTPException(status_code=500, detail="Twilio OTP service not configured")
        
        # Send OTP using Twilio Verify
        verification = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone_number,
            channel='sms'
        )
        
        return {
            "message": "OTP sent successfully", 
            "status": verification.status,
            "phone_number": phone_number
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for missing phone number)
        raise
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@app.post("/api/verify-otp")
async def verify_otp(request: dict):
    """Verify OTP using Twilio"""
    try:
        phone_number = request.get("phone_number")
        otp = request.get("otp")
        user_type = request.get("user_type", "seller")
        
        if not phone_number or not otp:
            raise HTTPException(status_code=400, detail="Phone number and OTP are required")
        
        if not twilio_client or not TWILIO_VERIFY_SERVICE_SID:
            raise HTTPException(status_code=500, detail="Twilio OTP service not configured")
        
        # Verify OTP using Twilio Verify
        verification_check = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=phone_number,
            code=otp
        )
        
        if verification_check.status == 'approved':
            # Check if user exists
            user = db.users.find_one({"phone_number": phone_number})
            if not user:
                # Create new user
                user_id = str(uuid.uuid4())
                user = {
                    "user_id": user_id,
                    "phone_number": phone_number,
                    "user_type": user_type,
                    "created_at": datetime.utcnow()
                }
                db.users.insert_one(user)
            
            # Remove MongoDB ObjectId for JSON serialization
            if '_id' in user:
                del user['_id']
            
            # Generate JWT token
            token = jwt.encode({
                "user_id": user["user_id"],
                "phone_number": phone_number,
                "user_type": user["user_type"],
                "exp": datetime.utcnow() + timedelta(hours=24)
            }, JWT_SECRET, algorithm="HS256")
            
            return {"message": "OTP verified successfully", "token": token, "user": user}
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP")
            
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for missing params or invalid OTP)
        raise
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

@app.post("/api/post-land")
async def post_land(
    title: str = Form(...),
    area: str = Form(...),
    price: str = Form(...),
    description: str = Form(...),
    latitude: str = Form(...),
    longitude: str = Form(...),
    photos: List[UploadFile] = File(default=[]),
    videos: List[UploadFile] = File(default=[]),
    user_id: str = Depends(verify_jwt_token)
):
    """Post a new land listing"""
    try:
        # Upload photos to S3
        photo_urls = []
        for photo in photos:
            if photo.filename:
                content = await photo.read()
                filename = f"photos/{uuid.uuid4()}.{photo.filename.split('.')[-1]}"
                photo_url = upload_to_s3(content, filename, photo.content_type)
                if photo_url:
                    photo_urls.append(photo_url)
        
        # Upload videos to S3
        video_urls = []
        for video in videos:
            if video.filename:
                content = await video.read()
                filename = f"videos/{uuid.uuid4()}.{video.filename.split('.')[-1]}"
                video_url = upload_to_s3(content, filename, video.content_type)
                if video_url:
                    video_urls.append(video_url)
        
        # Create listing
        listing_id = str(uuid.uuid4())
        listing = {
            "listing_id": listing_id,
            "seller_id": user_id,
            "title": title,
            "area": area,
            "price": price,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "photos": photo_urls,
            "videos": video_urls,
            "status": "pending_payment",
            "created_at": datetime.utcnow()
        }
        
        db.listings.insert_one(listing)
        
        return {"message": "Land listing created successfully", "listing_id": listing_id}
    except Exception as e:
        print(f"Error posting land: {e}")
        raise HTTPException(status_code=500, detail="Failed to post land listing")

@app.get("/api/my-listings")
async def get_my_listings(user_id: str = Depends(verify_jwt_token)):
    """Get listings for the authenticated user"""
    try:
        listings = list(db.listings.find({"seller_id": user_id}))
        for listing in listings:
            listing['_id'] = str(listing['_id'])
        return {"listings": listings}
    except Exception as e:
        print(f"Error getting listings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get listings")

@app.get("/api/listings")
async def get_listings():
    """Get all active listings"""
    try:
        listings = list(db.listings.find({"status": "active"}))
        for listing in listings:
            listing['_id'] = str(listing['_id'])
        return {"listings": listings}
    except Exception as e:
        print(f"Error getting listings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get listings")

@app.post("/api/create-payment-order")
async def create_payment_order(request: PaymentRequest, user_id: str = Depends(verify_jwt_token)):
    """Create Razorpay payment order"""
    try:
        if razorpay_client:
            order = razorpay_client.order.create({
                "amount": request.amount * 100,  # Amount in paisa
                "currency": request.currency,
                "receipt": f"receipt_{request.listing_id}",
                "payment_capture": 1
            })
            
            # Save payment record
            payment_record = {
                "payment_id": str(uuid.uuid4()),
                "listing_id": request.listing_id,
                "seller_id": user_id,
                "amount": request.amount,
                "currency": request.currency,
                "razorpay_order_id": order['id'],
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            db.payments.insert_one(payment_record)
            
            return {"order": order}
        else:
            return {"message": "Payment service not configured"}
    except Exception as e:
        print(f"Error creating payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

@app.post("/api/verify-payment")
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    user_id: str = Depends(verify_jwt_token)
):
    """Verify Razorpay payment"""
    try:
        if razorpay_client:
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
                
                # Update payment record
                db.payments.update_one(
                    {"razorpay_order_id": razorpay_order_id},
                    {"$set": {
                        "status": "completed",
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                # Find and activate listing
                payment = db.payments.find_one({"razorpay_order_id": razorpay_order_id})
                if payment:
                    db.listings.update_one(
                        {"listing_id": payment["listing_id"]},
                        {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
                    )
                
                return {"message": "Payment verified successfully"}
            except Exception as e:
                return {"message": "Payment verification failed"}
        else:
            return {"message": "Payment service not configured"}
    except Exception as e:
        print(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")

@app.post("/api/broker-signup")
async def broker_signup(broker: BrokerSignup):
    """Register a new broker"""
    try:
        # Check if broker already exists
        existing_broker = db.brokers.find_one({"phone_number": broker.phone_number})
        if existing_broker:
            return {"message": "Broker already registered"}
        
        broker_id = str(uuid.uuid4())
        broker_data = {
            "broker_id": broker_id,
            "name": broker.name,
            "agency": broker.agency,
            "phone_number": broker.phone_number,
            "email": broker.email,
            "photo": broker.photo,
            "created_at": datetime.utcnow()
        }
        
        db.brokers.insert_one(broker_data)
        
        return {"message": "Broker registered successfully", "broker_id": broker_id}
    except Exception as e:
        print(f"Error registering broker: {e}")
        raise HTTPException(status_code=500, detail="Failed to register broker")

@app.get("/api/broker-dashboard")
async def broker_dashboard():
    """Get broker dashboard data"""
    try:
        listings = list(db.listings.find({"status": "active"}))
        for listing in listings:
            listing['_id'] = str(listing['_id'])
        return {"listings": listings}
    except Exception as e:
        print(f"Error getting broker dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get broker dashboard")

# Admin routes
@app.post("/api/admin/login")
async def admin_login(request: AdminLogin):
    """Admin login"""
    try:
        if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
            token = jwt.encode({
                "user_type": "admin",
                "username": request.username,
                "exp": datetime.utcnow() + timedelta(hours=8)
            }, JWT_SECRET, algorithm="HS256")
            
            return {"message": "Admin login successful", "token": token}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        print(f"Error in admin login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/api/admin/stats")
async def admin_stats(admin: dict = Depends(verify_admin_token)):
    """Get admin dashboard statistics"""
    try:
        total_users = db.users.count_documents({})
        total_listings = db.listings.count_documents({})
        active_listings = db.listings.count_documents({"status": "active"})
        pending_listings = db.listings.count_documents({"status": "pending_payment"})
        total_brokers = db.brokers.count_documents({})
        total_payments = db.payments.count_documents({})
        completed_payments = db.payments.count_documents({"status": "completed"})
        
        return {
            "total_users": total_users,
            "total_listings": total_listings,
            "active_listings": active_listings,
            "pending_listings": pending_listings,
            "total_brokers": total_brokers,
            "total_payments": total_payments,
            "completed_payments": completed_payments
        }
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get admin stats")

@app.get("/api/admin/users")
async def admin_users(admin: dict = Depends(verify_admin_token)):
    """Get all users for admin"""
    try:
        users = list(db.users.find({}))
        for user in users:
            user['_id'] = str(user['_id'])
        return {"users": users}
    except Exception as e:
        print(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get users")

@app.get("/api/admin/listings")
async def admin_listings(admin: dict = Depends(verify_admin_token)):
    """Get all listings for admin"""
    try:
        listings = list(db.listings.find({}))
        for listing in listings:
            listing['_id'] = str(listing['_id'])
        return {"listings": listings}
    except Exception as e:
        print(f"Error getting admin listings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get listings")

@app.get("/api/admin/brokers")
async def admin_brokers(admin: dict = Depends(verify_admin_token)):
    """Get all brokers for admin"""
    try:
        brokers = list(db.brokers.find({}))
        for broker in brokers:
            broker['_id'] = str(broker['_id'])
        return {"brokers": brokers}
    except Exception as e:
        print(f"Error getting admin brokers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get brokers")

@app.get("/api/admin/payments")
async def admin_payments(admin: dict = Depends(verify_admin_token)):
    """Get all payments for admin"""
    try:
        payments = list(db.payments.find({}))
        for payment in payments:
            payment['_id'] = str(payment['_id'])
        return {"payments": payments}
    except Exception as e:
        print(f"Error getting admin payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payments")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)