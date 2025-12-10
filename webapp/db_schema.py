"""
MongoDB Schema Definition and Initialization
This module defines the database schema and creates necessary indexes
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
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
    #     "created_by": str,        # Email of user who created the space
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
        ("created_at", DESCENDING),
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
    db.reviews.create_index([("space_id", ASCENDING), ("timestamp", DESCENDING)])
    print("✓ Created compound index on reviews.space_id + timestamp")

    # Additional indexes
    db.reviews.create_index([("timestamp", DESCENDING)])
    print("✓ Created index on reviews.timestamp")

    db.reviews.create_index([("rating", ASCENDING)])
    print("✓ Created index on reviews.rating")

    # Add indexes for vote sorting
    db.reviews.create_index([("upvotes", DESCENDING)])
    print("✓ Created index on reviews.upvotes")
    db.reviews.create_index([("downvotes", ASCENDING)])
    print("✓ Created index on reviews.downvotes")

    # ==================== REVIEW_VOTES COLLECTION ====================
    # Schema for review_votes collection (tracks individual user votes)
    # {
    #     "_id": ObjectId,
    #     "review_id": str,         # Reference to review _id
    #     "user_email": str,        # Email of user who voted
    #     "vote_type": str,         # "upvote" or "downvote"
    #     "timestamp": datetime     # When vote was cast
    # }

    if "review_votes" not in db.list_collection_names():
        db.create_collection("review_votes")
        print("✓ Created 'review_votes' collection")

    # Create indexes for review_votes collection
    db.review_votes.create_index([("review_id", ASCENDING), ("user_email", ASCENDING)], unique=True)
    print("✓ Created unique compound index on review_votes.review_id + user_email")
    db.review_votes.create_index([("review_id", ASCENDING)])
    print("✓ Created index on review_votes.review_id")

    # ==================== STUDY_SPACE_REQUESTS COLLECTION ====================
    # Schema for study_space_requests collection
    # {
    #     "_id": ObjectId,
    #     "building": str,              # Requested building name
    #     "sublocation": str,            # Requested sublocation
    #     "status": str,                # "pending", "approved", "rejected"
    #     "requested_by": str,          # User's email
    #     "requester_netid": str,       # User's netid
    #     "requested_at": datetime,     # When request was submitted
    #     "processed_at": datetime,     # When request was approved/rejected
    #     "processed_by": str,          # Admin email who processed it
    #     "rejection_reason": str       # Optional reason for rejection
    # }

    if "study_space_requests" not in db.list_collection_names():
        db.create_collection("study_space_requests")
        print("Created 'study_space_requests' collection")

    # Create indexes for study_space_requests collection
    db.study_space_requests.create_index([("status", ASCENDING)])
    print("Created index on study_space_requests.status")

    db.study_space_requests.create_index([("requested_at", DESCENDING)])
    print("Created index on study_space_requests.requested_at")

    db.study_space_requests.create_index([("requested_by", ASCENDING)])
    print("Created index on study_space_requests.requested_by")

    print("\nDatabase schema setup complete!")
    print(f"Database: {db.name}")
    print(f"Collections: {', '.join(db.list_collection_names())}")


if __name__ == "__main__":
    create_collections_and_indexes()
