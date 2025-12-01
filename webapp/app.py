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

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get(
    "MONGO_URI", "mongodb://localhost:27017/nyu_printers"
)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, email, user_id=None):
        self.id = user_id or email  # Use email as ID
        self.email = email
        self.netid = (
            email.split("@")[0] if "@" in email else email
        )  # Extract netid from email


@login_manager.user_loader
def load_user(user_id):
    """Load user from database"""
    user = mongo.db.users.find_one({"email": user_id})
    if user:
        return User(email=user["email"], user_id=str(user["_id"]))
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
    user_obj = User(email=user["email"], user_id=str(user["_id"]))
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
    return jsonify(
        {
            "email": current_user.email,
            "netid": current_user.netid,
        }
    )


@app.route("/logout")
def logout():
    """Logout route"""
    logout_user()
    session.clear()
    return redirect(url_for("index"))


@app.route("/")
def index():
    """Home page showing all printer statuses based on most recent user reports"""
    printers = list(mongo.db.printers.find())

    # Get the most recent report for each printer
    for printer in printers:
        reports = list(
            mongo.db.reports.find({"printer_id": str(printer["_id"])})
            .sort("timestamp", -1)
            .limit(1)
        )

        if reports:
            printer["status"] = reports[0]["status"]
            printer["paper_level"] = reports[0].get("paper_level", 0)
            printer["toner_level"] = reports[0].get("toner_level", 0)
            printer["last_updated"] = reports[0]["timestamp"]
            printer["reported_by"] = reports[0].get("reported_by", "Anonymous")
        else:
            printer["status"] = "unknown"
            printer["paper_level"] = 0
            printer["toner_level"] = 0
            printer["last_updated"] = None
            printer["reported_by"] = None

    return render_template("index.html", printers=printers)

@app.route("/api/printers", methods=["GET"])
def get_printers():
    """API endpoint to get all printers"""
    try:
        printers = list(mongo.db.printers.find())

        for printer in printers:
            printer["_id"] = str(printer["_id"])
        return jsonify(printers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/printers/<printer_id>", methods=["GET"])
def get_printer(printer_id):
    """API endpoint to get a specific printer with its most recent report"""
    try:
        query = {"_id": ObjectId(printer_id)}
    except (InvalidId, TypeError):
        # If not a valid ObjectId, use string query (for tests)
        query = {"_id": printer_id}

    printer = mongo.db.printers.find_one(query)
    if printer:
        printer["_id"] = str(printer["_id"])

        # Get most recent report
        recent_report = mongo.db.reports.find_one(
            {"printer_id": printer_id}, sort=[("timestamp", -1)]
        )

        if recent_report:
            printer["status"] = recent_report["status"]
            printer["paper_level"] = recent_report.get("paper_level", 0)
            printer["toner_level"] = recent_report.get("toner_level", 0)
            printer["last_updated"] = recent_report["timestamp"]
            printer["reported_by"] = recent_report.get("reported_by", "Anonymous")

        # Get recent reports history
        reports = list(
            mongo.db.reports.find({"printer_id": printer_id})
            .sort("timestamp", -1)
            .limit(10)
        )

        for report in reports:
            report["_id"] = str(report["_id"])

        printer["recent_reports"] = reports

        return jsonify(printer)
    return jsonify({"error": "Printer not found"}), 404


@app.route("/api/printers", methods=["POST"])
def add_printer():
    """API endpoint to add a new printer"""
    data = request.get_json()

    if not data or "name" not in data or "location" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    printer = {
        "name": data.get("name"),
        "location": data.get("location"),
        "building": data.get("building"),
        "floor": data.get("floor"),
        "created_at": datetime.utcnow(),
    }
    try:
        result = mongo.db.printers.insert_one(printer)
        printer["_id"] = str(result.inserted_id)
        return jsonify(printer), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/printers/<printer_id>", methods=["PUT"])
def update_printer(printer_id):
    """API endpoint to update printer info (not status - use reports for that)"""
    data = request.get_json()
    update_data = {}

    if "status" in data:
        update_data["status"] = data["status"]
    if "paper_level" in data:
        update_data["paper_level"] = data["paper_level"]

    if update_data:
        update_data["updated_at"] = datetime.utcnow()

        try:
            query = {"_id": ObjectId(printer_id)}
        except (InvalidId, TypeError):
            # If not a valid ObjectId, use string query (for tests)
            query = {"_id": printer_id}

        try:
            result = mongo.db.printers.update_one(query, {"$set": update_data})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        if result.matched_count:
            return jsonify({"message": "Printer updated successfully"})
        return jsonify({"error": "Printer not found"}), 404

    return jsonify({"error": "No valid fields to update"}), 400


@app.route("/api/printers/<printer_id>", methods=["DELETE"])
def delete_printer(printer_id):
    """API endpoint to delete a printer"""
    try:
        query = {"_id": ObjectId(printer_id)}
    except (InvalidId, TypeError):
        # If not a valid ObjectId, use string query (for tests)
        query = {"_id": printer_id}
    try:
        result = mongo.db.printers.delete_one(query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    if result.deleted_count:
        return jsonify({"message": "Printer deleted successfully"})
    return jsonify({"error": "Printer not found"}), 404


@app.route("/api/reports", methods=["POST"])
@login_required
def submit_report():
    """API endpoint for users to submit printer status reports (requires authentication)"""
    data = request.get_json()

    # Validate required fields
    if not data.get("printer_id") or not data.get("status"):
        return jsonify({"error": "printer_id and status are required"}), 400

    # Verify printer exists
    printer = mongo.db.printers.find_one({"_id": ObjectId(data["printer_id"])})
    if not printer:
        return jsonify({"error": "Printer not found"}), 404

    # Use authenticated user's NetID (override any provided reported_by)
    report = {
        "printer_id": data["printer_id"],
        "status": data[
            "status"
        ],  # available, busy, offline, out_of_paper, out_of_toner
        "paper_level": data.get("paper_level", 0),
        "toner_level": data.get("toner_level", 0),
        "reported_by": current_user.netid,  # Authenticated NetID (extracted from email)
        "reporter_email": current_user.email,  # Email
        "comments": data.get("comments", ""),
        "timestamp": datetime.utcnow(),
    }

    result = mongo.db.reports.insert_one(report)
    report["_id"] = str(result.inserted_id)

    return jsonify(report), 201


@app.route("/api/reports", methods=["GET"])
def get_reports():
    """API endpoint to get all reports (most recent first)"""
    printer_id = request.args.get("printer_id")
    limit = int(request.args.get("limit", 50))

    query = {}
    if printer_id:
        query["printer_id"] = printer_id

    reports = list(mongo.db.reports.find(query).sort("timestamp", -1).limit(limit))

    for report in reports:
        report["_id"] = str(report["_id"])

    return jsonify(reports)


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
