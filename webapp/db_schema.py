"""
MongoDB Schema Definition and Initialization
This module defines the database schema and creates necessary indexes
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
import os

def get_db_connection():
    """Get MongoDB connection"""
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nyu_study_spaces")
    client = MongoClient(MONGO_URI)
    return client.get_database()

def create_collections_and_indexes():
    """
    Create collections and indexes for the NYU Study Space Status application
    """
    db = get_db_connection()
    
    # ==================== STUDY_SPACES COLLECTION ====================
    # Schema for study_spaces collection
    # {
    #     "_id": ObjectId,
    #     "building": str,          # e.g., "Bobst Library"
    #     "sublocation": str,       # e.g., "2nd Floor Study Area"
    #     "created_at": datetime,   # When space was added to system
    #     "updated_at": datetime    # Last time space info was updated
    # }
    
    if "study_spaces" not in db.list_collection_names():
        db.create_collection("study_spaces")
        print("Created 'study_spaces' collection")
    
    # Create indexes for study_spaces collection
    study_spaces_indexes = [
        ("building", ASCENDING),
        ("sublocation", ASCENDING),
        ("created_at", DESCENDING)
    ]
    
    for field, order in study_spaces_indexes:
        db.study_spaces.create_index([(field, order)])
        print(f"✓ Created index on study_spaces.{field}")
    
    # ==================== REVIEWS COLLECTION ====================
    # Schema for reviews collection
    # {
    #     "_id": ObjectId,
    #     "space_id": str,                # Reference to study_space _id
    #     "rating": int,                  # 1-5 overall rating
    #     "silence": int,                 # 1-5 silence level
    #     "crowdedness": int,             # 1-5 crowdedness level
    #     "review": str,                  # Text review/comments
    #     "reported_by": str,             # Username or NetID
    #     "reporter_email": str,          # User's email
    #     "timestamp": datetime           # When review was submitted
    # }
    
    if "reviews" not in db.list_collection_names():
        db.create_collection("reviews")
        print("✓ Created 'reviews' collection")
    
    # Create indexes for reviews collection
    # Most important: space_id and timestamp for fetching recent reviews
    db.reviews.create_index([
        ("space_id", ASCENDING),
        ("timestamp", DESCENDING)
    ])
    print("✓ Created compound index on reviews.space_id + timestamp")
    
    # Additional indexes
    db.reviews.create_index([("timestamp", DESCENDING)])
    print("✓ Created index on reviews.timestamp")
    
    db.reviews.create_index([("rating", ASCENDING)])
    print("✓ Created index on reviews.rating")
    
    print("\nDatabase schema setup complete!")
    print(f"Database: {db.name}")
    print(f"Collections: {', '.join(db.list_collection_names())}")

if __name__ == "__main__":
    create_collections_and_indexes()
