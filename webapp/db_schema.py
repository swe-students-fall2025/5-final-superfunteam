"""
MongoDB Schema Definition and Initialization
This module defines the database schema and creates necessary indexes
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
import os

def get_db_connection():
    """Get MongoDB connection"""
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nyu_printers")
    client = MongoClient(MONGO_URI)
    return client.get_database()

def create_collections_and_indexes():
    """
    Create collections and indexes for the NYU Printer Status application
    """
    db = get_db_connection()
    
    # ==================== PRINTERS COLLECTION ====================
    # Schema for printers collection
    # {
    #     "_id": ObjectId,
    #     "name": str,              # e.g., "Bobst Library Printer"
    #     "location": str,          # e.g., "Bobst Library - 2nd Floor"
    #     "building": str,          # e.g., "Bobst Library"
    #     "floor": str,             # e.g., "2"
    #     "created_at": datetime,   # When printer was added to system
    #     "updated_at": datetime    # Last time printer info was updated
    # }
    
    if "printers" not in db.list_collection_names():
        db.create_collection("printers")
        print("✓ Created 'printers' collection")
    
    # Create indexes for printers collection
    printers_indexes = [
        ("name", ASCENDING),
        ("location", ASCENDING),
        ("building", ASCENDING),
        ("created_at", DESCENDING)
    ]
    
    for field, order in printers_indexes:
        db.printers.create_index([(field, order)])
        print(f"✓ Created index on printers.{field}")
    
    # ==================== REPORTS COLLECTION ====================
    # Schema for reports collection
    # {
    #     "_id": ObjectId,
    #     "printer_id": str,              # Reference to printer _id
    #     "status": str,                  # "available", "busy", "offline", "out_of_paper", "out_of_toner"
    #     "paper_level": int,             # 0-100 percentage
    #     "toner_level": int,             # 0-100 percentage
    #     "reported_by": str,             # Username or "Anonymous"
    #     "comments": str,                # Optional user comments
    #     "timestamp": datetime           # When report was submitted
    # }
    
    if "reports" not in db.list_collection_names():
        db.create_collection("reports")
        print("✓ Created 'reports' collection")
    
    # Create indexes for reports collection
    # Most important: printer_id and timestamp for fetching recent reports
    db.reports.create_index([
        ("printer_id", ASCENDING),
        ("timestamp", DESCENDING)
    ])
    print("✓ Created compound index on reports.printer_id + timestamp")
    
    # Additional indexes
    db.reports.create_index([("timestamp", DESCENDING)])
    print("✓ Created index on reports.timestamp")
    
    db.reports.create_index([("status", ASCENDING)])
    print("✓ Created index on reports.status")
    
    print("\n✅ Database schema setup complete!")
    print(f"Database: {db.name}")
    print(f"Collections: {', '.join(db.list_collection_names())}")

if __name__ == "__main__":
    create_collections_and_indexes()
