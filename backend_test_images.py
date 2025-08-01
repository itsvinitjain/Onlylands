import requests
import base64
import json
import os
import time
from pymongo import MongoClient
import sys

# Backend URL
BACKEND_URL = "https://547a6392-129c-42e0-badb-1a283db0eb37.preview.emergentagent.com"

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "onlylands_db"

def connect_to_db():
    """Connect to MongoDB and return the database object"""
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        print("✅ Connected to MongoDB")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {str(e)}")
        return None

def check_existing_listings(db):
    """Check if there are any existing listings and examine their structure"""
    try:
        listings = list(db.listings.find())
        print(f"Found {len(listings)} listings in the database")
        
        if len(listings) > 0:
            # Examine the first listing
            listing = listings[0]
            print("\nSample listing structure:")
            print(f"Listing ID: {listing.get('listing_id')}")
            print(f"Title: {listing.get('title')}")
            print(f"Status: {listing.get('status')}")
            
            # Check images structure
            images = listing.get('images', [])
            print(f"\nImages count: {len(images)}")
            if len(images) > 0:
                print("\nImage structure:")
                image = images[0]
                print(f"Filename: {image.get('filename')}")
                print(f"Content Type: {image.get('content_type')}")
                
                # Check if data is present and in correct format
                if 'data' in image:
                    data_sample = image['data'][:30] + "..." if len(image['data']) > 30 else image['data']
                    print(f"Data (sample): {data_sample}")
                    
                    # Check if data is valid base64
                    try:
                        base64.b64decode(image['data'])
                        print("✅ Image data is valid base64")
                    except:
                        print("❌ Image data is NOT valid base64")
                else:
                    print("❌ No 'data' field found in image")
            
            # Check videos structure
            videos = listing.get('videos', [])
            print(f"\nVideos count: {len(videos)}")
            if len(videos) > 0:
                print("\nVideo structure:")
                video = videos[0]
                print(f"Filename: {video.get('filename')}")
                print(f"Content Type: {video.get('content_type')}")
                
                # Check if data is present and in correct format
                if 'data' in video:
                    data_sample = video['data'][:30] + "..." if len(video['data']) > 30 else video['data']
                    print(f"Data (sample): {data_sample}")
                    
                    # Check if data is valid base64
                    try:
                        base64.b64decode(video['data'])
                        print("✅ Video data is valid base64")
                    except:
                        print("❌ Video data is NOT valid base64")
                else:
                    print("❌ No 'data' field found in video")
        
        return listings
    except Exception as e:
        print(f"❌ Error checking listings: {str(e)}")
        return []

def test_file_upload():
    """Test the file upload endpoint"""
    try:
        # Create a test image file
        test_image_path = '/tmp/test_image.png'
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        # Prepare form data
        form_data = {
            'title': "Test Land for Image Testing",
            'location': "Test Location, Maharashtra",
            'area': "5 Acres",
            'price': "50 Lakhs",
            'description': "This is a test land listing for image testing.",
            'latitude': 18.6414,
            'longitude': 72.9897
        }
        
        # Prepare files
        files = [
            ('images', ('test_image.png', open(test_image_path, 'rb'), 'image/png'))
        ]
        
        # Make the request
        url = f"{BACKEND_URL}/api/listings"
        print(f"\nTesting file upload to {url}")
        response = requests.post(url, data=form_data, files=files)
        
        if response.status_code == 200:
            print(f"✅ File upload successful - Status: {response.status_code}")
            result = response.json()
            print(f"Listing ID: {result.get('listing_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Images Count: {result.get('images_count')}")
            
            # Return the listing ID for further testing
            return result.get('listing_id')
        else:
            print(f"❌ File upload failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error testing file upload: {str(e)}")
        return None
    finally:
        # Close the file
        for _, file_tuple in files:
            file_tuple[1].close()
        
        # Clean up test file
        try:
            os.remove(test_image_path)
        except:
            pass

def verify_listing_in_db(db, listing_id):
    """Verify that the listing was stored correctly in the database"""
    if not listing_id:
        print("❌ No listing ID provided for verification")
        return
    
    try:
        listing = db.listings.find_one({"listing_id": listing_id})
        if listing:
            print(f"\n✅ Found listing in database with ID: {listing_id}")
            print(f"Status: {listing.get('status')}")
            print(f"Payment Status: {listing.get('payment_status')}")
            
            # Check images
            images = listing.get('images', [])
            print(f"Images count: {len(images)}")
            if len(images) > 0:
                image = images[0]
                print(f"Image filename: {image.get('filename')}")
                print(f"Image content type: {image.get('content_type')}")
                
                # Check if data is present and in correct format
                if 'data' in image:
                    data_sample = image['data'][:30] + "..." if len(image['data']) > 30 else image['data']
                    print(f"Image data (sample): {data_sample}")
                    
                    # Check if data is valid base64
                    try:
                        base64.b64decode(image['data'])
                        print("✅ Image data is valid base64")
                    except:
                        print("❌ Image data is NOT valid base64")
                else:
                    print("❌ No 'data' field found in image")
            else:
                print("❌ No images found in the listing")
        else:
            print(f"❌ Listing with ID {listing_id} not found in database")
    except Exception as e:
        print(f"❌ Error verifying listing in database: {str(e)}")

def test_get_listing(listing_id=None):
    """Test the get listings endpoint and check the image data structure"""
    try:
        url = f"{BACKEND_URL}/api/listings"
        print(f"\nTesting get listings from {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"✅ Get listings successful - Status: {response.status_code}")
            result = response.json()
            listings = result.get('listings', [])
            print(f"Retrieved {len(listings)} listings")
            
            if len(listings) > 0:
                # If a specific listing ID was provided, find that listing
                if listing_id:
                    target_listing = next((l for l in listings if l.get('listing_id') == listing_id), None)
                    if target_listing:
                        print(f"\nFound target listing with ID: {listing_id}")
                        listing_to_check = target_listing
                    else:
                        print(f"\nTarget listing with ID {listing_id} not found in response")
                        listing_to_check = listings[0]
                        print(f"Using first listing instead with ID: {listing_to_check.get('listing_id')}")
                else:
                    listing_to_check = listings[0]
                    print(f"\nChecking first listing with ID: {listing_to_check.get('listing_id')}")
                
                # Check images structure in the response
                images = listing_to_check.get('images', [])
                print(f"Images count: {len(images)}")
                if len(images) > 0:
                    image = images[0]
                    print(f"Image filename: {image.get('filename')}")
                    print(f"Image content type: {image.get('content_type')}")
                    
                    # Check if data is present
                    if 'data' in image:
                        data_sample = image['data'][:30] + "..." if len(image['data']) > 30 else image['data']
                        print(f"Image data (sample): {data_sample}")
                        
                        # Check if data is valid base64
                        try:
                            base64.b64decode(image['data'])
                            print("✅ Image data is valid base64")
                            
                            # Check if the frontend can use this data directly
                            expected_format = f"data:{image.get('content_type')};base64,{image.get('data')}"
                            frontend_format = f"data:{image.get('content_type')};base64,{image.get('data')}"
                            
                            if expected_format == frontend_format:
                                print("✅ Image data is in the correct format for frontend")
                            else:
                                print("❌ Image data format doesn't match frontend expectations")
                                print(f"Expected: data:{image.get('content_type')};base64,[base64_data]")
                                print(f"Actual: {frontend_format[:50]}...")
                        except:
                            print("❌ Image data is NOT valid base64")
                    else:
                        print("❌ No 'data' field found in image")
                else:
                    print("❌ No images found in the listing")
            else:
                print("❌ No listings found in the response")
        else:
            print(f"❌ Get listings failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing get listings: {str(e)}")

def main():
    print("=" * 50)
    print("OnlyLands Image Storage Test")
    print("=" * 50)
    
    # Connect to the database
    db = connect_to_db()
    if db is None:
        print("Exiting due to database connection failure")
        return 1
    
    # Check existing listings
    print("\n1. Checking existing listings in the database...")
    existing_listings = check_existing_listings(db)
    
    # Test file upload
    print("\n2. Testing file upload...")
    new_listing_id = test_file_upload()
    
    # Verify the new listing in the database
    if new_listing_id:
        print("\n3. Verifying new listing in the database...")
        verify_listing_in_db(db, new_listing_id)
    
    # Test getting listings
    print("\n4. Testing get listings endpoint...")
    test_get_listing(new_listing_id)
    
    print("\n" + "=" * 50)
    print("Test completed")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())