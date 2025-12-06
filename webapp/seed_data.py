"""
Seed Data Script for NYU Study Space Status Application
Populates the database with sample NYU study space locations
"""

from pymongo import MongoClient
from datetime import datetime
import os

def get_db_connection():
    """Get MongoDB connection"""
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nyu_study_spaces")
    client = MongoClient(MONGO_URI)
    return client.get_database()

def seed_study_spaces():
    """Insert sample NYU study space locations into the database"""
    db = get_db_connection()
    
    # Sample NYU study space locations across campus
    sample_spaces = [
        {
            "building": "Bobst Library",
            "sublocation": "1st Floor Study Area",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Bobst Library",
            "sublocation": "2nd Floor Quiet Zone",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Bobst Library",
            "sublocation": "3rd Floor Group Study Rooms",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Bobst Library",
            "sublocation": "12th Floor Lounge",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Kimmel Center",
            "sublocation": "2nd Floor Student Lounge",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Kimmel Center",
            "sublocation": "Market Dining Area",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Courant Institute",
            "sublocation": "Warren Weaver Hall - Room 101",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Courant Institute",
            "sublocation": "Common Area Lounge",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Stern School of Business",
            "sublocation": "Tisch Hall Library",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Stern School of Business",
            "sublocation": "Kaufman Center Study Rooms",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Silver Center",
            "sublocation": "1st Floor Atrium",
            "created_at": datetime.utcnow(),
        },
        {
            "building": "Tandon School of Engineering",
            "sublocation": "Rogers Hall 3rd Floor",
            "created_at": datetime.utcnow(),
        },
    ]
    
    # Check if spaces already exist
    existing_count = db.study_spaces.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Database already contains {existing_count} study spaces.")
        print("Skipping seed operation to preserve existing data.")
        print("To reseed, manually clear the database first.")
        return
    
    # Insert sample study spaces
    result = db.study_spaces.insert_many(sample_spaces)
    print(f"✅ Successfully inserted {len(result.inserted_ids)} study spaces!")
    
    # Display inserted spaces
    print("\n📍 Sample Study Space Locations:")
    for i, space in enumerate(sample_spaces, 1):
        print(f"{i}. {space['building']} - {space['sublocation']}")
    
    print()
    
    # Add some sample reviews for demonstration
    if len(result.inserted_ids) > 0:
        sample_reviews = [
            {
                "space_id": str(result.inserted_ids[0]),
                "rating": 4,
                "silence": 3,
                "crowdedness": 4,
                "review": "Great space for collaborative work, can get a bit noisy during peak hours",
                "reported_by": "student1",
                "reporter_email": "student1@nyu.edu",
                "timestamp": datetime.utcnow()
            },
            {
                "space_id": str(result.inserted_ids[1]),
                "rating": 5,
                "silence": 5,
                "crowdedness": 2,
                "review": "Perfect for deep focus work. Very quiet and peaceful!",
                "reported_by": "student2",
                "reporter_email": "student2@nyu.edu",
                "timestamp": datetime.utcnow()
            },
            {
                "space_id": str(result.inserted_ids[2]),
                "rating": 4,
                "silence": 2,
                "crowdedness": 4,
                "review": "Great for group projects, rooms can be reserved in advance",
                "reported_by": "student3",
                "reporter_email": "student3@nyu.edu",
                "timestamp": datetime.utcnow()
            },
            {
                "space_id": str(result.inserted_ids[3]),
                "rating": 5,
                "silence": 4,
                "crowdedness": 1,
                "review": "Amazing views and usually not crowded. Hidden gem!",
                "reported_by": "student4",
                "reporter_email": "student4@nyu.edu",
                "timestamp": datetime.utcnow()
            },
            {
                "space_id": str(result.inserted_ids[4]),
                "rating": 3,
                "silence": 2,
                "crowdedness": 5,
                "review": "Social atmosphere but too crowded and noisy for serious studying",
                "reported_by": "student5",
                "reporter_email": "student5@nyu.edu",
                "timestamp": datetime.utcnow()
            },
            {
                "space_id": str(result.inserted_ids[8]),
                "rating": 5,
                "silence": 4,
                "crowdedness": 2,
                "review": "Excellent business library with comfortable seating and quiet atmosphere",
                "reported_by": "student6",
                "reporter_email": "student6@nyu.edu",
                "timestamp": datetime.utcnow()
            }
        ]
        
        db.reviews.insert_many(sample_reviews)
        print(f"✅ Added {len(sample_reviews)} sample reviews!")

if __name__ == "__main__":
    print("🌱 NYU Study Space Status - Database Seed Script")
    print("=" * 50)
    seed_study_spaces()
