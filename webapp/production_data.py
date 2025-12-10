"""
Production Data Script for NYU Printer Status Application
Replace sample data with actual NYU printer locations for production deployment

INSTRUCTIONS:
1. Research actual NYU printer locations by visiting:
   - Libraries (Bobst, Tamiment, etc.)
   - Computer labs
   - Student centers
   - Residence halls
   
2. Replace the sample data below with real printer information 

3. Run this script ONCE during production deployment:
   docker-compose run --rm setup-production
   
   OR manually:
   python production_data.py
"""

from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Get MongoDB connection"""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        mongodb_host = os.getenv("MONGODB_HOST", "localhost")
        mongodb_port = os.getenv("MONGODB_PORT", "27017")
        mongo_uri = f"mongodb://{mongodb_host}:{mongodb_port}/"
    
    # Get database name from environment or use default
    database_name = os.getenv("MONGODB_DATABASE", "proj4")
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        db = client[database_name]
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

def insert_production_printers():
    """Insert real NYU printer locations into the database"""
    db = get_db_connection()
    
    production_printers = [
        # Bobst Library
        {
            "name": "Bobst Library - Ground Floor Reference Printer",
            "location": "Elmer Holmes Bobst Library - Ground Floor, Near Reference Desk",
            "building": "Bobst Library",
            "floor": "Ground",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Bobst Library - 2nd Floor North Printer",
            "location": "Elmer Holmes Bobst Library - 2nd Floor, North Wing",
            "building": "Bobst Library",
            "floor": "2",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        
        # Kimmel Center
        {
            "name": "Kimmel Center - Room 406 Computer Lab",
            "location": "Kimmel Center for University Life - Room 406",
            "building": "Kimmel Center",
            "floor": "4",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        
        # Add more real locations here...
        # {
        #     "name": "REAL_PRINTER_NAME",
        #     "location": "EXACT_LOCATION_WITH_ROOM_NUMBER",
        #     "building": "BUILDING_NAME",
        #     "floor": "FLOOR_NUMBER",
        #     "created_at": datetime.utcnow(),
        #     "updated_at": datetime.utcnow()
        # },
    ]
    
    # ============================================================
    # VALIDATION
    # ============================================================
    if len(production_printers) < 5:
        print("⚠️  WARNING: Only {} printers defined.".format(len(production_printers)))
        print("Please add more real printer locations before production deployment.")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Production data insertion cancelled")
            return
    
    # Check if data already exists
    existing_count = db.printers.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Database already contains {existing_count} printers.")
        print("Production data should only be inserted into an empty database.")
        response = input("Clear existing data and insert production data? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Production data insertion cancelled")
            return
        
        # Clear existing data
        db.printers.delete_many({})
        db.reports.delete_many({})
        print("✓ Cleared existing data")
    
    # Insert production printers
    result = db.printers.insert_many(production_printers)
    print(f"✅ Successfully inserted {len(result.inserted_ids)} production printers!")
    
    # Display inserted printers
    print("\n📍 Production Printer Locations:")
    for i, printer in enumerate(production_printers, 1):
        print(f"{i}. {printer['name']}")
        print(f"   Location: {printer['location']}")
        print()
    
    print("\n" + "="*60)
    print("✅ PRODUCTION DATA SETUP COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Verify printers appear correctly on the website")
    print("2. Ask users to submit initial status reports")
    print("3. Monitor for any missing or incorrect locations")
    print("4. Update this script as new printers are added to campus")

if __name__ == "__main__":
    print("🏢 NYU Printer Status - Production Data Setup")
    print("=" * 60)
    print("⚠️  WARNING: This will replace sample data with production data")
    print("=" * 60)
    insert_production_printers()
