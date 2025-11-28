"""
Seed Data Script for NYU Printer Status Application
Populates the database with sample NYU printer locations
"""

from pymongo import MongoClient
from datetime import datetime
import os

def get_db_connection():
    """Get MongoDB connection"""
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nyu_printers")
    client = MongoClient(MONGO_URI)
    return client.get_database()

def seed_printers():
    """Insert sample NYU printer locations into the database"""
    db = get_db_connection()
    
    # Sample NYU printer locations across campus
    sample_printers = [
        {
            "name": "Bobst Library - Main Floor Printer",
            "location": "Elmer Holmes Bobst Library - 1st Floor",
            "building": "Bobst Library",
            "floor": "1",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Bobst Library - Second Floor Printer",
            "location": "Elmer Holmes Bobst Library - 2nd Floor",
            "building": "Bobst Library",
            "floor": "2",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Kimmel Center - Student Lounge Printer",
            "location": "Kimmel Center for University Life - 2nd Floor Student Lounge",
            "building": "Kimmel Center",
            "floor": "2",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Courant Institute - Computer Lab Printer",
            "location": "Warren Weaver Hall - Room 101",
            "building": "Courant Institute",
            "floor": "1",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Tandon School - Rogers Hall Printer",
            "location": "Rogers Hall - 3rd Floor Computer Lab",
            "building": "Tandon School of Engineering",
            "floor": "3",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Stern School - Tisch Hall Printer",
            "location": "Henry Kaufman Management Center - 2nd Floor",
            "building": "Stern School of Business",
            "floor": "2",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Silver Center - Student Services Printer",
            "location": "Silver Center - 1st Floor Student Services",
            "building": "Silver Center",
            "floor": "1",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Palladium - Residence Hall Printer",
            "location": "Palladium Athletic Facility - Lobby",
            "building": "Palladium",
            "floor": "1",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Torch Club - Graduate Lounge Printer",
            "location": "Torch Club - Graduate Student Lounge",
            "building": "Torch Club",
            "floor": "2",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Lipton Hall - Computer Lab Printer",
            "location": "Lipton Hall - Basement Computer Lab",
            "building": "Lipton Hall",
            "floor": "B",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Check if printers already exist
    existing_count = db.printers.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Database already contains {existing_count} printers.")
        print("Skipping seed operation to preserve existing data.")
        print("To reseed, manually clear the database first.")
        return
    
    # Insert sample printers
    result = db.printers.insert_many(sample_printers)
    print(f"✅ Successfully inserted {len(result.inserted_ids)} printers!")
    
    # Display inserted printers
    print("\n📍 Sample Printer Locations:")
    for i, printer in enumerate(sample_printers, 1):
        print(f"{i}. {printer['name']}")
        print(f"   Location: {printer['location']}")
        print()
    
    # Add some sample reports for demonstration
    if len(result.inserted_ids) > 0:
        sample_reports = [
            {
                "printer_id": str(result.inserted_ids[0]),
                "status": "available",
                "paper_level": 85,
                "toner_level": 70,
                "reported_by": "Anonymous",
                "comments": "Working perfectly",
                "timestamp": datetime.utcnow()
            },
            {
                "printer_id": str(result.inserted_ids[1]),
                "status": "busy",
                "paper_level": 60,
                "toner_level": 45,
                "reported_by": "Student",
                "comments": "Currently printing a large job",
                "timestamp": datetime.utcnow()
            },
            {
                "printer_id": str(result.inserted_ids[2]),
                "status": "available",
                "paper_level": 90,
                "toner_level": 80,
                "reported_by": "Staff",
                "comments": "Recently refilled",
                "timestamp": datetime.utcnow()
            }
        ]
        
        db.reports.insert_many(sample_reports)
        print(f"✅ Added {len(sample_reports)} sample status reports!")

if __name__ == "__main__":
    print("🌱 NYU Printer Status - Database Seed Script")
    print("=" * 50)
    seed_printers()
