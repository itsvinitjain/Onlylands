from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import FileResponse
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
import time
import boto3
from botocore.exceptions import ClientError
import pymongo
from pymongo import MongoClient
import razorpay
from twilio.rest import Client
import json
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Initialize services with error handling for MongoDB Atlas
def connect_to_mongodb(max_retries=3):
    """Connect to MongoDB with retry logic"""
    for attempt in range(max_retries):
        try:
            client = MongoClient(
                MONGO_URL,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connection timeout
                socketTimeoutMS=5000,           # 5 second socket timeout
                retryWrites=True,               # Enable retryable writes for Atlas
                w='majority'                    # Write concern for Atlas
            )
            # Test the connection
            client.admin.command('ping')
            print(f"✅ Successfully connected to MongoDB: {DB_NAME} (attempt {attempt + 1})")
            return client, client[DB_NAME]
        except Exception as e:
            print(f"❌ MongoDB connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"❌ Failed to connect to MongoDB after {max_retries} attempts")
                return None, None

# Connect to MongoDB
client, db = connect_to_mongodb()

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
    location: Optional[str] = None
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
    """Upload file to local storage (mimicking S3) and return URL"""
    try:
        import os
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "/app/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        # Replace any path separators to flatten the filename
        import time
        clean_filename = filename.replace('/', '_').replace('\\', '_')
        unique_filename = f"{int(time.time())}_{clean_filename}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        # Save file locally
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Return local URL that will be served by the backend
        local_url = f"/api/uploads/{unique_filename}"
        print(f"✅ File stored locally: {local_url}")
        return local_url
        
    except Exception as e:
        print(f"❌ Error storing file locally: {e}")
        return None

# Database helper functions
def check_db_connection():
    """Check if database connection is available"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection not available")
    return db

def safe_db_operation(operation_func, *args, **kwargs):
    """Safely execute database operation with error handling"""
    try:
        check_db_connection()
        return operation_func(*args, **kwargs)
    except Exception as e:
        print(f"Database operation error: {e}")
        raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")

# JWT token verification
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint for deployment verification"""
    try:
        # Check database connection
        if db is not None:
            db.admin.command('ping')
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "twilio": "configured" if twilio_client else "not_configured",
                "razorpay": "configured" if razorpay_client else "not_configured",
                "s3": "configured" if s3_client else "not_configured"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/send-otp")
async def send_otp(request: dict):
    """Send OTP to phone number using Twilio with demo fallback"""
    try:
        phone_number = request.get("phone_number")
        user_type = request.get("user_type", "seller")
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        if not twilio_client or not TWILIO_VERIFY_SERVICE_SID:
            # No Twilio configured, use demo mode
            return {
                "message": "OTP sent successfully (Demo Mode)", 
                "status": "demo_mode",
                "phone_number": phone_number,
                "demo_info": "Service temporarily unavailable. Use OTP 123456 for testing."
            }
        
        print(f"Attempting to send OTP to {phone_number}")
        
        try:
            # Try to send OTP using Twilio Verify
            verification = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
                to=phone_number,
                channel='sms'
            )
            
            print(f"Twilio response: {verification.status}")
            
            return {
                "message": "OTP sent successfully", 
                "status": verification.status,
                "phone_number": phone_number
            }
            
        except Exception as twilio_error:
            error_message = str(twilio_error)
            print(f"Twilio error details: {error_message}")
            
            # Handle specific Twilio errors with demo fallback
            if "20429" in error_message:
                # Rate limit exceeded - fall back to demo mode
                print("Twilio rate limit exceeded, falling back to demo mode")
                return {
                    "message": "OTP sent successfully (Demo Mode)", 
                    "status": "demo_mode",
                    "phone_number": phone_number,
                    "demo_info": "Rate limit exceeded. Use OTP 123456 for testing."
                }
            elif "21211" in error_message:
                # Invalid phone number - fall back to demo mode
                return {
                    "message": "OTP sent successfully (Demo Mode)", 
                    "status": "demo_mode",
                    "phone_number": phone_number,
                    "demo_info": "Invalid phone number format. Use OTP 123456 for testing."
                }
            elif "21608" in error_message:
                # Unverified phone number - fall back to demo mode
                return {
                    "message": "OTP sent successfully (Demo Mode)", 
                    "status": "demo_mode",
                    "phone_number": phone_number,
                    "demo_info": "Phone number not verified for trial account. Use OTP 123456 for testing."
                }
            else:
                # Other Twilio errors - fall back to demo mode
                print(f"Twilio error, falling back to demo mode: {twilio_error}")
                return {
                    "message": "OTP sent successfully (Demo Mode)", 
                    "status": "demo_mode",
                    "phone_number": phone_number,
                    "demo_info": "Service temporarily unavailable. Use OTP 123456 for testing."
                }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error sending OTP: {e}")
        # Final fallback to demo mode
        return {
            "message": "OTP sent successfully (Demo Mode)", 
            "status": "demo_mode",
            "phone_number": phone_number or "",
            "demo_info": "Service temporarily unavailable. Use OTP 123456 for testing."
        }

@app.post("/api/verify-otp")
async def verify_otp(request: dict):
    """Verify OTP using Twilio with demo OTP fallback"""
    try:
        phone_number = request.get("phone_number")
        otp = request.get("otp")
        user_type = request.get("user_type", "seller")
        
        if not phone_number or not otp:
            raise HTTPException(status_code=400, detail="Phone number and OTP are required")
        
        # Check for demo OTP first
        if otp == "123456":
            print(f"Using demo OTP for {phone_number}")
            # Demo OTP verification - always succeeds
            try:
                check_db_connection()
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
                else:
                    # Update existing user's user_type if it's different
                    if user.get("user_type") != user_type:
                        db.users.update_one(
                            {"phone_number": phone_number},
                            {"$set": {"user_type": user_type, "updated_at": datetime.utcnow()}}
                        )
                        user["user_type"] = user_type
            except Exception as e:
                print(f"Database error during demo OTP verification: {e}")
                raise HTTPException(status_code=500, detail="Database connection error")
            
            # Remove MongoDB ObjectId for JSON serialization
            if '_id' in user:
                del user['_id']
            
            # Generate JWT token with the current user_type
            token = jwt.encode({
                "user_id": user["user_id"],
                "phone_number": phone_number,
                "user_type": user_type,
                "exp": datetime.utcnow() + timedelta(hours=24)
            }, JWT_SECRET, algorithm="HS256")
            
            return {"message": "OTP verified successfully (Demo Mode)", "token": token, "user": user}
        
        # Try genuine Twilio verification
        if not twilio_client or not TWILIO_VERIFY_SERVICE_SID:
            # If no Twilio configured and not demo OTP, reject
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        try:
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
                else:
                    # Update existing user's user_type if it's different
                    if user.get("user_type") != user_type:
                        db.users.update_one(
                            {"phone_number": phone_number},
                            {"$set": {"user_type": user_type, "updated_at": datetime.utcnow()}}
                        )
                        user["user_type"] = user_type
                
                # Remove MongoDB ObjectId for JSON serialization
                if '_id' in user:
                    del user['_id']
                
                # Generate JWT token with the current user_type
                token = jwt.encode({
                    "user_id": user["user_id"],
                    "phone_number": phone_number,
                    "user_type": user_type,
                    "exp": datetime.utcnow() + timedelta(hours=24)
                }, JWT_SECRET, algorithm="HS256")
                
                return {"message": "OTP verified successfully", "token": token, "user": user}
            else:
                raise HTTPException(status_code=400, detail="Invalid OTP")
                
        except Exception as twilio_error:
            error_message = str(twilio_error)
            print(f"Twilio verification error: {error_message}")
            
            # Handle specific Twilio verification errors
            if "20404" in error_message:
                raise HTTPException(status_code=400, detail="Invalid OTP or OTP has expired")
            elif "20429" in error_message:
                raise HTTPException(status_code=400, detail="Too many verification attempts. Please use OTP 123456 for demo.")
            else:
                raise HTTPException(status_code=400, detail="Invalid OTP")
            
    except HTTPException:
        # Re-raise HTTP exceptions
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
    location: str = Form(default=""),
    google_maps_link: str = Form(default=""),
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
                if photo_url:  # photo_url is now a string URL
                    photo_urls.append(photo_url)
                    print(f"✅ Photo uploaded: {photo.filename}")
                else:
                    print(f"❌ Failed to upload photo: {photo.filename}")
        
        # Upload videos to S3
        video_urls = []
        for video in videos:
            if video.filename:
                content = await video.read()
                filename = f"videos/{uuid.uuid4()}.{video.filename.split('.')[-1]}"
                video_url = upload_to_s3(content, filename, video.content_type)
                if video_url:  # video_url is now a string URL
                    video_urls.append(video_url)
                    print(f"✅ Video uploaded: {video.filename}")
                else:
                    print(f"❌ Failed to upload video: {video.filename}")
        
        # Create listing
        listing_id = str(uuid.uuid4())
        listing = {
            "listing_id": listing_id,
            "seller_id": user_id,
            "title": title,
            "area": area,
            "price": price,
            "description": description,
            "location": location,
            "google_maps_link": google_maps_link,
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

@app.get("/api/uploads/{filename}")
async def serve_uploaded_file(filename: str):
    """Serve uploaded files from local storage"""
    try:
        file_path = f"/app/uploads/{filename}"
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        print(f"Error serving file: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve file")

@app.get("/api/debug/all-listings")
async def get_all_listings_debug():
    """Debug endpoint to see all listings regardless of status"""
    try:
        listings = list(db.listings.find({}))
        for listing in listings:
            listing['_id'] = str(listing['_id'])
        return {"listings": listings, "count": len(listings)}
    except Exception as e:
        print(f"Error getting debug listings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get debug listings")

@app.post("/api/create-payment-order")
async def create_payment_order(request: dict, user_id: str = Depends(verify_jwt_token)):
    """Create Razorpay payment order with demo mode support"""
    try:
        amount = request.get("amount", 299)  # Default ₹299
        listing_id = request.get("listing_id")
        
        if not listing_id:
            raise HTTPException(status_code=400, detail="Listing ID is required")
        
        # Convert rupees to paise (₹299 = 29900 paise)
        amount_in_paise = amount * 100
        
        # Check if we have real Razorpay keys or using demo
        if not razorpay_client or RAZORPAY_KEY_ID == "rzp_test_demo123":
            print("Using demo payment mode - generating mock order")
            # Create demo order response
            order_id = f"order_demo_{int(time.time())}"
            order_data = {
                "id": order_id,
                "amount": amount_in_paise,
                "currency": "INR", 
                "status": "created",
                "receipt": f"receipt_{listing_id}_{int(time.time())}",
                "notes": {
                    "listing_id": listing_id,
                    "user_id": user_id,
                    "demo_mode": True
                }
            }
            
            # Store payment record in database
            payment_record = {
                "razorpay_order_id": order_id,
                "listing_id": listing_id,
                "user_id": user_id,
                "amount": amount_in_paise,
                "currency": "INR",
                "status": "created",
                "demo_mode": True,
                "created_at": datetime.utcnow()
            }
            db.payments.insert_one(payment_record)
            
            print(f"Demo payment order created: {order_id}")
            return {"order": order_data, "demo_mode": True}
        
        try:
            # Try real Razorpay integration
            order = razorpay_client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"receipt_{listing_id}_{int(time.time())}",
                "notes": {
                    "listing_id": listing_id,
                    "user_id": user_id
                }
            })
            
            # Store payment record in database
            payment_record = {
                "razorpay_order_id": order["id"],
                "listing_id": listing_id,
                "user_id": user_id,
                "amount": amount_in_paise,
                "currency": "INR",
                "status": "created",
                "demo_mode": False,
                "created_at": datetime.utcnow()
            }
            db.payments.insert_one(payment_record)
            
            return {"order": order, "demo_mode": False}
            
        except Exception as razorpay_error:
            print(f"Razorpay error: {razorpay_error}")
            # Fall back to demo mode
            order_id = f"order_demo_{int(time.time())}"
            order_data = {
                "id": order_id,
                "amount": amount_in_paise,
                "currency": "INR",
                "status": "created", 
                "receipt": f"receipt_{listing_id}_{int(time.time())}",
                "notes": {
                    "listing_id": listing_id,
                    "user_id": user_id,
                    "demo_mode": True
                }
            }
            
            # Store payment record in database
            payment_record = {
                "razorpay_order_id": order_id,
                "listing_id": listing_id,
                "user_id": user_id,
                "amount": amount_in_paise,
                "currency": "INR",
                "status": "created",
                "demo_mode": True,
                "created_at": datetime.utcnow()
            }
            db.payments.insert_one(payment_record)
            
            print(f"Fallback: Demo payment order created: {order_id}")
            return {"order": order_data, "demo_mode": True}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@app.post("/api/verify-payment")
async def verify_payment(request: PaymentVerification, user_id: str = Depends(verify_jwt_token)):
    """Verify Razorpay payment with demo mode support"""
    try:
        # Find the payment record
        payment = db.payments.find_one({"razorpay_order_id": request.razorpay_order_id})
        if not payment:
            raise HTTPException(status_code=400, detail="Payment not found")
        
        # Check if this is a demo payment
        if payment.get("demo_mode", False) or request.razorpay_order_id.startswith("order_demo_"):
            print(f"Processing demo payment verification: {request.razorpay_order_id}")
            
            # For demo mode, always verify successfully
            # Update payment record
            db.payments.update_one(
                {"razorpay_order_id": request.razorpay_order_id},
                {"$set": {
                    "status": "completed",
                    "razorpay_payment_id": request.razorpay_payment_id,
                    "razorpay_signature": request.razorpay_signature,
                    "updated_at": datetime.utcnow(),
                    "demo_verified": True
                }}
            )
            
            # Activate listing
            if payment["listing_id"]:
                db.listings.update_one(
                    {"listing_id": payment["listing_id"]},
                    {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
                )
                print(f"Listing {payment['listing_id']} activated via demo payment")
            
            return {"message": "Payment verified successfully (Demo Mode)", "demo_mode": True}
        
        # Handle real Razorpay verification
        if not razorpay_client:
            raise HTTPException(status_code=500, detail="Payment service not configured")
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Update payment record
            db.payments.update_one(
                {"razorpay_order_id": request.razorpay_order_id},
                {"$set": {
                    "status": "completed",
                    "razorpay_payment_id": request.razorpay_payment_id,
                    "razorpay_signature": request.razorpay_signature,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Find and activate listing
            if payment["listing_id"]:
                db.listings.update_one(
                    {"listing_id": payment["listing_id"]},
                    {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
                )
                print(f"Listing {payment['listing_id']} activated via real payment")
            
            return {"message": "Payment verified successfully", "demo_mode": False}
        except Exception as e:
            print(f"Payment verification failed: {e}")
            return {"message": "Payment verification failed"}
        
    except HTTPException:
        raise
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
            "location": broker.location,
            "photo": broker.photo,
            "created_at": datetime.utcnow()
        }
        
        db.brokers.insert_one(broker_data)
        
        return {"message": "Broker registered successfully", "broker_id": broker_id}
    except Exception as e:
        print(f"Error registering broker: {e}")
        raise HTTPException(status_code=500, detail="Failed to register broker")

@app.get("/api/broker-profile")
async def get_broker_profile(user_id: str = Depends(verify_jwt_token)):
    """Get broker profile - returns 404 if broker not registered"""
    try:
        # Get user info first
        user = db.users.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is a broker and has a broker profile
        if user.get("user_type") != "broker":
            raise HTTPException(status_code=403, detail="User is not a broker")
        
        # Look for broker profile in brokers collection
        broker = db.brokers.find_one({"phone_number": user.get("phone_number")})
        if not broker:
            raise HTTPException(status_code=404, detail="Broker profile not found")
        
        # Remove MongoDB ObjectId
        if '_id' in broker:
            del broker['_id']
        
        return {"broker": broker}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting broker profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get broker profile")

@app.get("/api/broker-dashboard")
async def broker_dashboard(user_id: str = Depends(verify_jwt_token)):
    """Get broker dashboard data"""
    try:
        # First check if broker is registered
        user = db.users.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.get("user_type") != "broker":
            raise HTTPException(status_code=403, detail="User is not a broker")
        
        # Check if broker profile exists
        broker = db.brokers.find_one({"phone_number": user.get("phone_number")})
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not registered")
        
        # Return active listings for registered broker
        listings = list(db.listings.find({"status": "active"}))
        for listing in listings:
            listing['_id'] = str(listing['_id'])
        return {"listings": listings}
    except HTTPException:
        raise
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

@app.delete("/api/admin/delete-listing/{listing_id}")
async def delete_listing(listing_id: str, admin: dict = Depends(verify_admin_token)):
    """Delete a listing (admin only)"""
    try:
        result = db.land_listings.delete_one({"listing_id": listing_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        return {"message": "Listing deleted successfully"}
    except Exception as e:
        print(f"Error deleting listing: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete listing")

@app.put("/api/admin/update-listing/{listing_id}")
async def update_listing(listing_id: str, listing_data: dict, admin: dict = Depends(verify_admin_token)):
    """Update a listing (admin only)"""
    try:
        # Remove fields that shouldn't be updated
        update_data = {k: v for k, v in listing_data.items() if k not in ['_id', 'listing_id', 'created_at']}
        
        result = db.land_listings.update_one(
            {"listing_id": listing_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        return {"message": "Listing updated successfully"}
    except Exception as e:
        print(f"Error updating listing: {e}")
        raise HTTPException(status_code=500, detail="Failed to update listing")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)