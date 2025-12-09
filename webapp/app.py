from typing import Any
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_pymongo import PyMongo
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from bcrypt import hashpw, checkpw, gensalt
from bson.objectid import ObjectId
from bson.errors import InvalidId
import os
from datetime import datetime
from functools import wraps
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# MongoDB configuration
mongo_uri = os.getenv("MONGO_URI")

# When running tests, avoid parsing SRV URIs that require DNS lookups
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("FLASK_ENV") == "test":
    mongo_uri = "mongodb://localhost:27017/testdb"
if not mongo_uri:
    mongodb_host = os.getenv("MONGODB_HOST", "localhost")
    mongodb_port = os.getenv("MONGODB_PORT", "27017")
    mongo_uri = f"mongodb://{mongodb_host}:{mongodb_port}/"

# Get database name from environment or use default
database_name = os.getenv("MONGODB_DATABASE", "proj4")

# Construct full URI with database name if not already included
# If URI ends with /, add database name. Otherwise, assume it's already in the URI (like Atlas URIs)
if mongo_uri.endswith("/"):
    mongo_uri = f"{mongo_uri}{database_name}"

app.config["MONGO_URI"] = mongo_uri
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")

mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, email, user_id=None, display_name=None):
        self.id = user_id or email  # Use email as ID
        self.email = email
        self.netid = (
            email.split("@")[0] if "@" in email else email
        )  # Extract netid from email
        self.display_name = display_name


@login_manager.user_loader
def load_user(user_id):
    """Load user from database using either Mongo _id or email stored in session"""
    queries = []

    try:
        queries.append({"_id": ObjectId(user_id)})
    except (InvalidId, TypeError):
        pass

    # Fallback for any sessions that might have stored the email directly
    queries.append({"email": user_id})

    for query in queries:
        user = mongo.db.users.find_one(query)
        if user:
            return User(
                email=user["email"], 
                user_id=str(user.get("_id", user["email"])),
                display_name=user.get("display_name")
            )
    return None


def validate_nyu_email(email):
    """Validate that email ends with @nyu.edu"""
    if not email or not isinstance(email, str):
        return False
    return email.lower().endswith("@nyu.edu")


@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user with NYU email and password"""
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate email is NYU email
    if not validate_nyu_email(email):
        return jsonify({"error": "Email must be a valid NYU email (@nyu.edu)"}), 400

    # Validate password
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if user already exists
    existing_user = mongo.db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400

    # Extract netid from email
    netid = email.split("@")[0]

    # Create new user
    user = {
        "email": email,
        "password_hash": hashpw(password.encode("utf-8"), gensalt()).decode("utf-8"),
        "netid": netid,
    }

    result = mongo.db.users.insert_one(user)
    user["_id"] = str(result.inserted_id)
    del user["password_hash"]  # Don't return password hash

    return jsonify({"message": "User registered successfully", "user": user}), 201


@app.route("/login")
def login_page():
    """Login page"""
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def login():
    """Login with email and password"""
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Find user in database
    user = mongo.db.users.find_one({"email": email})

    if not user or not checkpw(
        password.encode("utf-8"), user["password_hash"].encode("utf-8")
    ):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create User object and log in
    user_obj = User(
        email=user["email"], 
        user_id=str(user["_id"]),
        display_name=user.get("display_name")
    )
    login_user(user_obj)

    return jsonify(
        {
            "message": "Login successful",
            "user": {
                "email": user["email"],
                "netid": user.get("netid"),
            },
        }
    )


@app.route("/api/user", methods=["GET"])
@login_required
def get_current_user():
    """Get current authenticated user information"""
    # Fetch fresh user data from database
    user = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user:
        # Fallback to email if ObjectId fails
        user = mongo.db.users.find_one({"email": current_user.email})
    
    return jsonify(
        {
            "email": current_user.email,
            "netid": current_user.netid,
            "display_name": user.get("display_name") if user else None,
        }
    )


@app.route("/api/user", methods=["PUT"])
@login_required
def update_user_profile():
    """Update user profile (password and/or display name)"""
    data = request.get_json()
    
    # Find user in database
    try:
        query = {"_id": ObjectId(current_user.id)}
    except (InvalidId, TypeError):
        query = {"email": current_user.email}
    
    user = mongo.db.users.find_one(query)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    update_data = {}
    
    # Update password if provided
    if "password" in data and data["password"]:
        new_password = data["password"]
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Verify current password if provided
        if "current_password" in data and data["current_password"]:
            if not checkpw(
                data["current_password"].encode("utf-8"),
                user["password_hash"].encode("utf-8")
            ):
                return jsonify({"error": "Current password is incorrect"}), 401
        
        update_data["password_hash"] = hashpw(new_password.encode("utf-8"), gensalt()).decode("utf-8")
    
    # Update display name if provided
    if "display_name" in data:
        display_name = data["display_name"].strip() if data["display_name"] else None
        # Allow empty string to clear display name
        if display_name == "":
            display_name = None
        update_data["display_name"] = display_name
    
    if not update_data:
        return jsonify({"error": "No fields to update"}), 400
    
    # Update user in database
    mongo.db.users.update_one(query, {"$set": update_data})
    
    # Update current_user object if display_name changed
    if "display_name" in update_data:
        current_user.display_name = update_data["display_name"]
    
    return jsonify({"message": "Profile updated successfully"}), 200


@app.route("/profile")
@login_required
def profile_page():
    """Profile page for users to change password and display name"""
    return render_template("profile.html")


@app.route("/logout")
def logout():
    """Logout route"""
    logout_user()
    session.clear()
    return redirect(url_for("index"))


@app.route("/")
def index():
    """Home page showing all study spaces with their average ratings"""
    spaces = list(mongo.db.study_spaces.find())

    # Get average ratings and recent review for each space
    for space in spaces:
        reviews = list(
            mongo.db.reviews.find({"space_id": str(space["_id"])})
            .sort("timestamp", -1)
        )

        if reviews:
            # Calculate averages
            avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
            avg_silence = sum(r["silence"] for r in reviews) / len(reviews)
            avg_crowdedness = sum(r["crowdedness"] for r in reviews) / len(reviews)
            
            space["avg_rating"] = round(avg_rating, 1)
            space["avg_silence"] = round(avg_silence, 1)
            space["avg_crowdedness"] = round(avg_crowdedness, 1)
            space["review_count"] = len(reviews)
            space["last_updated"] = reviews[0]["timestamp"]
            space["last_review"] = reviews[0].get("review", "")
            space["reported_by"] = reviews[0].get("reported_by", "Anonymous")
        else:
            space["avg_rating"] = 0
            space["avg_silence"] = 0
            space["avg_crowdedness"] = 0
            space["review_count"] = 0
            space["last_updated"] = None
            space["last_review"] = ""
            space["reported_by"] = None

    return render_template("index.html", spaces=spaces)


@app.route("/add-space")
def add_space_page():
    """Page for manually adding a new study space"""
    return render_template("add_space.html")


@app.route("/map")
def map_page():
    """Page showing study spaces on Google Maps"""
    spaces = list(mongo.db.study_spaces.find())
    
    # Format spaces for display
    for space in spaces:
        space["_id"] = str(space["_id"])
        # Create a search query for Google Maps (building + sublocation)
        space["map_query"] = f"{space.get('building', '')} {space.get('sublocation', '')} NYU"
    
    return render_template("map.html", spaces=spaces)


@app.route("/api/spaces", methods=["GET"])
def get_spaces():
    """API endpoint to get all study spaces"""
    try:
        spaces = list[Any](mongo.db.study_spaces.find())

        for space in spaces:
            space["_id"] = str(space["_id"])
        return jsonify(spaces)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/spaces/<space_id>", methods=["GET"])
def get_space(space_id):
    """API endpoint to get a specific study space with its reviews"""
    try:
        query = {"_id": ObjectId(space_id)}
    except (InvalidId, TypeError):
        # If not a valid ObjectId, use string query (for tests)
        query = {"_id": space_id}

    space = mongo.db.study_spaces.find_one(query)
    if space:
        space["_id"] = str(space["_id"])

        # Get all reviews for this space
        reviews = list(
            mongo.db.reviews.find({"space_id": space_id})
            .sort("timestamp", -1)
            .limit(20)
        )

        for review in reviews:
            review["_id"] = str(review["_id"])

        # Calculate averages
        if reviews:
            avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
            avg_silence = sum(r["silence"] for r in reviews) / len(reviews)
            avg_crowdedness = sum(r["crowdedness"] for r in reviews) / len(reviews)
            
            space["avg_rating"] = round(avg_rating, 1)
            space["avg_silence"] = round(avg_silence, 1)
            space["avg_crowdedness"] = round(avg_crowdedness, 1)
            space["review_count"] = len(reviews)
        else:
            space["avg_rating"] = 0
            space["avg_silence"] = 0
            space["avg_crowdedness"] = 0
            space["review_count"] = 0

        space["reviews"] = reviews

        return jsonify(space)
    return jsonify({"error": "Study space not found"}), 404


@app.route("/api/spaces", methods=["POST"])
def add_space():
    """API endpoint to add a new study space"""
    data = request.get_json()

    if not data or "building" not in data or "sublocation" not in data:
        return jsonify({"error": "Missing required fields: building and sublocation"}), 400
    
    space = {
        "building": data.get("building"),
        "sublocation": data.get("sublocation"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    try:
        result = mongo.db.study_spaces.insert_one(space)
        space["_id"] = str(result.inserted_id)
        space_id = str(result.inserted_id)
        
        # If silence and crowdedness are provided and user is authenticated, create initial review
        silence = data.get("silence")
        crowdedness = data.get("crowdedness")
        if silence is not None and crowdedness is not None and current_user.is_authenticated:
            try:
                silence = int(silence)
                crowdedness = int(crowdedness)
                
                if 1 <= silence <= 5 and 1 <= crowdedness <= 5:
                    # Create initial review with default rating (average of silence and crowdedness)
                    # or use a default rating of 3
                    initial_rating = 3  # Default rating
                    
                    review = {
                        "space_id": space_id,
                        "rating": initial_rating,
                        "silence": silence,
                        "crowdedness": crowdedness,
                        "review": f"Initial review for {data.get('building')} - {data.get('sublocation')}",
                        "reported_by": current_user.netid,
                        "reporter_email": current_user.email,
                        "timestamp": datetime.utcnow(),
                    }
                    mongo.db.reviews.insert_one(review)
            except (ValueError, TypeError):
                # Invalid values, skip review creation
                pass
        
        return jsonify(space), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/spaces/<space_id>", methods=["PUT"])
def update_space(space_id):
    """API endpoint to update study space info"""
    data = request.get_json()
    update_data = {}

    if "building" in data:
        update_data["building"] = data["building"]
    if "sublocation" in data:
        update_data["sublocation"] = data["sublocation"]

    if update_data:
        update_data["updated_at"] = datetime.utcnow()

        try:
            query = {"_id": ObjectId(space_id)}
        except (InvalidId, TypeError):
            # If not a valid ObjectId, use string query (for tests)
            query = {"_id": space_id}

        try:
            result = mongo.db.study_spaces.update_one(query, {"$set": update_data})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        if result.matched_count:
            return jsonify({"message": "Study space updated successfully"})
        return jsonify({"error": "Study space not found"}), 404

    return jsonify({"error": "No valid fields to update"}), 400


@app.route("/api/spaces/<space_id>", methods=["DELETE"])
def delete_space(space_id):
    """API endpoint to delete a study space"""
    try:
        query = {"_id": ObjectId(space_id)}
    except (InvalidId, TypeError):
        # If not a valid ObjectId, use string query (for tests)
        query = {"_id": space_id}
    try:
        result = mongo.db.study_spaces.delete_one(query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    if result.deleted_count:
        return jsonify({"message": "Study space deleted successfully"})
    return jsonify({"error": "Study space not found"}), 404


@app.route("/api/reviews", methods=["POST"])
@login_required
def submit_review():
    """API endpoint for users to submit study space reviews (requires authentication)"""
    data = request.get_json()

    # Validate required fields
    if not data.get("space_id"):
        return jsonify({"error": "space_id is required"}), 400
    
    if not all(key in data for key in ["rating", "silence", "crowdedness"]):
        return jsonify({"error": "rating, silence, and crowdedness are required"}), 400

    # Verify space exists
    space = mongo.db.study_spaces.find_one({"_id": ObjectId(data["space_id"])})
    if not space:
        return jsonify({"error": "Study space not found"}), 404

    # Validate rating values (1-5)
    try:
        rating = int(data["rating"])
        silence = int(data["silence"])
        crowdedness = int(data["crowdedness"])
        
        if not (1 <= rating <= 5 and 1 <= silence <= 5 and 1 <= crowdedness <= 5):
            return jsonify({"error": "All ratings must be between 1 and 5"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Ratings must be valid integers"}), 400

    # Use authenticated user's NetID
    review = {
        "space_id": data["space_id"],
        "rating": rating,
        "silence": silence,
        "crowdedness": crowdedness,
        "review": data.get("review", ""),
        "reported_by": current_user.netid,
        "reporter_email": current_user.email,
        "timestamp": datetime.utcnow(),
    }

    result = mongo.db.reviews.insert_one(review)
    review["_id"] = str(result.inserted_id)

    return jsonify(review), 201


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    """API endpoint to get all reviews (most recent first)"""
    space_id = request.args.get("space_id")
    limit = int(request.args.get("limit", 50))

    query = {}
    if space_id:
        query["space_id"] = space_id

    reviews = list(mongo.db.reviews.find(query).sort("timestamp", -1).limit(limit))

    for review in reviews:
        review["_id"] = str(review["_id"])

    return jsonify(reviews)


@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        mongo.db.command("ping")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
