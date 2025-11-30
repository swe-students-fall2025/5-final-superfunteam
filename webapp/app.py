from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from bson.errors import InvalidId
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nyu_printers")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Development mode flag (bypasses SAML for local testing)
DEVELOPMENT_MODE = os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true"

mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "saml_login"

# Simple User class for Flask-Login
class User(UserMixin):
    def __init__(self, netid, email=None, name=None, affiliation=None):
        self.id = netid
        self.netid = netid
        self.email = email
        self.name = name
        self.affiliation = affiliation

@login_manager.user_loader
def load_user(user_id):
    """Load user from session"""
    if 'saml_user_data' in session:
        user_data = session['saml_user_data']
        return User(
            netid=user_data.get('netid'),
            email=user_data.get('email'),
            name=user_data.get('name'),
            affiliation=user_data.get('affiliation')
        )
    return None

def prepare_flask_request(request):
    """Prepare Flask request for python3-saml"""
    url_data = {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': request.environ.get('SERVER_PORT'),
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }
    return url_data

def init_saml_auth(req):
    """Initialize SAML authentication"""
    saml_path = os.path.join(os.path.dirname(__file__), 'saml')
    auth = OneLogin_Saml2_Auth(req, custom_base_path=saml_path)
    return auth

@app.route('/saml/login')
def saml_login():
    """Initiate SAML SSO login with NYU Shibboleth"""
    if DEVELOPMENT_MODE:
        return redirect(url_for('dev_login'))
    
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.login())

@app.route('/saml/acs', methods=['POST'])
def saml_acs():
    """Assertion Consumer Service - handle SAML response from NYU"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    
    errors = auth.get_errors()
    if errors:
        app.logger.error(f"SAML errors: {errors}")
        return jsonify({'error': 'Authentication failed', 'details': errors}), 401
    
    if not auth.is_authenticated():
        return jsonify({'error': 'Authentication failed'}), 401
    
    # Get user attributes from SAML response
    attributes = auth.get_attributes()
    
    # Map NYU Shibboleth attributes
    netid = attributes.get('urn:oid:0.9.2342.19200300.100.1.1', [''])[0]  # uid
    email = attributes.get('urn:oid:0.9.2342.19200300.100.1.3', [''])[0]  # mail
    given_name = attributes.get('urn:oid:2.5.4.42', [''])[0]  # givenName
    surname = attributes.get('urn:oid:2.5.4.4', [''])[0]  # sn
    affiliation = attributes.get('urn:oid:1.3.6.1.4.1.5923.1.1.1.1', [''])[0]  # eduPersonAffiliation
    
    name = f"{given_name} {surname}".strip() or netid
    
    # Store user data in session
    session['saml_user_data'] = {
        'netid': netid,
        'email': email,
        'name': name,
        'affiliation': affiliation
    }
    session['saml_nameid'] = auth.get_nameid()
    session['saml_session_index'] = auth.get_session_index()
    
    # Log in user with Flask-Login
    user = User(netid=netid, email=email, name=name, affiliation=affiliation)
    login_user(user)
    
    # Redirect to original destination or home
    next_url = session.pop('next_url', None) or url_for('index')
    return redirect(next_url)

@app.route('/saml/metadata')
def saml_metadata():
    """Provide SAML Service Provider metadata"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)
    
    if errors:
        return jsonify({'error': 'Invalid metadata', 'details': errors}), 500
    
    return metadata, 200, {'Content-Type': 'text/xml'}

@app.route('/saml/sls')
def saml_sls():
    """Single Logout Service"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    
    url = auth.process_slo()
    errors = auth.get_errors()
    
    if errors:
        app.logger.error(f"SLO errors: {errors}")
    
    logout_user()
    session.clear()
    
    if url:
        return redirect(url)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logout route"""
    if DEVELOPMENT_MODE:
        logout_user()
        session.clear()
        return redirect(url_for('index'))
    
    # SAML Single Logout
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    
    name_id = session.get('saml_nameid')
    session_index = session.get('saml_session_index')
    
    return redirect(auth.logout(name_id=name_id, session_index=session_index))

# Development-only login (bypasses SAML)
@app.route('/dev-login')
def dev_login():
    """Development login - bypasses SAML authentication"""
    if not DEVELOPMENT_MODE:
        return jsonify({'error': 'Development mode not enabled'}), 403
    
    # Create test user
    test_netid = request.args.get('netid', 'test123')
    user = User(
        netid=test_netid,
        email=f"{test_netid}@nyu.edu",
        name=f"Test User ({test_netid})",
        affiliation="student"
    )
    
    session['saml_user_data'] = {
        'netid': user.netid,
        'email': user.email,
        'name': user.name,
        'affiliation': user.affiliation
    }
    
    login_user(user)
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Home page showing all printer statuses based on most recent user reports"""
    printers = list(mongo.db.printers.find())
    
    # Get the most recent report for each printer
    for printer in printers:
        reports = list(mongo.db.reports.find(
            {'printer_id': str(printer['_id'])}
        ).sort('timestamp', -1).limit(1))
        
        if reports:
            printer['status'] = reports[0]['status']
            printer['paper_level'] = reports[0].get('paper_level', 0)
            printer['toner_level'] = reports[0].get('toner_level', 0)
            printer['last_updated'] = reports[0]['timestamp']
            printer['reported_by'] = reports[0].get('reported_by', 'Anonymous')
        else:
            printer['status'] = 'unknown'
            printer['paper_level'] = 0
            printer['toner_level'] = 0
            printer['last_updated'] = None
            printer['reported_by'] = None
    
    return render_template('index.html', printers=printers)

@app.route('/api/printers', methods=['GET'])
def get_printers():
    """API endpoint to get all printers"""
    printers = list(mongo.db.printers.find())
    # Convert ObjectId to string for JSON serialization
    for printer in printers:
        printer['_id'] = str(printer['_id'])
    return jsonify(printers)

@app.route('/api/printers/<printer_id>', methods=['GET'])
def get_printer(printer_id):
    """API endpoint to get a specific printer with its most recent report"""
    try:
        query = {'_id': ObjectId(printer_id)}
    except (InvalidId, TypeError):
        # If not a valid ObjectId, use string query (for tests)
        query = {'_id': printer_id}
    
    printer = mongo.db.printers.find_one(query)
    if printer:
        printer['_id'] = str(printer['_id'])
        
        # Get most recent report
        recent_report = mongo.db.reports.find_one(
            {'printer_id': printer_id},
            sort=[('timestamp', -1)]
        )
        
        if recent_report:
            printer['status'] = recent_report['status']
            printer['paper_level'] = recent_report.get('paper_level', 0)
            printer['toner_level'] = recent_report.get('toner_level', 0)
            printer['last_updated'] = recent_report['timestamp']
            printer['reported_by'] = recent_report.get('reported_by', 'Anonymous')
        
        # Get recent reports history
        reports = list(mongo.db.reports.find(
            {'printer_id': printer_id}
        ).sort('timestamp', -1).limit(10))
        
        for report in reports:
            report['_id'] = str(report['_id'])
        
        printer['recent_reports'] = reports
        
        return jsonify(printer)
    return jsonify({'error': 'Printer not found'}), 404

@app.route('/api/printers', methods=['POST'])
def add_printer():
    """API endpoint to add a new printer"""
    data = request.get_json()
    printer = {
        'name': data.get('name'),
        'location': data.get('location'),
        'building': data.get('building'),
        'floor': data.get('floor'),
        'created_at': datetime.utcnow()
    }
    result = mongo.db.printers.insert_one(printer)
    printer['_id'] = str(result.inserted_id)
    return jsonify(printer), 201

@app.route('/api/printers/<printer_id>', methods=['PUT'])
def update_printer(printer_id):
    """API endpoint to update printer info (not status - use reports for that)"""
    data = request.get_json()
    update_data = {}
    
    if 'name' in data:
        update_data['name'] = data['name']
    if 'location' in data:
        update_data['location'] = data['location']
    if 'building' in data:
        update_data['building'] = data['building']
    if 'floor' in data:
        update_data['floor'] = data['floor']
    
    if update_data:
        update_data['updated_at'] = datetime.utcnow()
        
        try:
            query = {'_id': ObjectId(printer_id)}
        except (InvalidId, TypeError):
            # If not a valid ObjectId, use string query (for tests)
            query = {'_id': printer_id}
        
        result = mongo.db.printers.update_one(
            query,
            {'$set': update_data}
        )
        
        if result.matched_count:
            return jsonify({'message': 'Printer updated successfully'})
        return jsonify({'error': 'Printer not found'}), 404
    
    return jsonify({'error': 'No valid fields to update'}), 400

@app.route('/api/printers/<printer_id>', methods=['DELETE'])
def delete_printer(printer_id):
    """API endpoint to delete a printer"""
    try:
        query = {'_id': ObjectId(printer_id)}
    except (InvalidId, TypeError):
        # If not a valid ObjectId, use string query (for tests)
        query = {'_id': printer_id}
    
    result = mongo.db.printers.delete_one(query)
    if result.deleted_count:
        return jsonify({'message': 'Printer deleted successfully'})
    return jsonify({'error': 'Printer not found'}), 404

@app.route('/api/reports', methods=['POST'])
@login_required
def submit_report():
    """API endpoint for users to submit printer status reports (requires authentication)"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('printer_id') or not data.get('status'):
        return jsonify({'error': 'printer_id and status are required'}), 400
    
    # Verify printer exists
    printer = mongo.db.printers.find_one({'_id': ObjectId(data['printer_id'])})
    if not printer:
        return jsonify({'error': 'Printer not found'}), 404
    
    # Use authenticated user's NetID (override any provided reported_by)
    report = {
        'printer_id': data['printer_id'],
        'status': data['status'],  # available, busy, offline, out_of_paper, out_of_toner
        'paper_level': data.get('paper_level', 0),
        'toner_level': data.get('toner_level', 0),
        'reported_by': current_user.netid,  # Authenticated NetID
        'reporter_name': current_user.name,  # Full name
        'reporter_email': current_user.email,  # Email
        'comments': data.get('comments', ''),
        'timestamp': datetime.utcnow()
    }
    
    result = mongo.db.reports.insert_one(report)
    report['_id'] = str(result.inserted_id)
    
    return jsonify(report), 201

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """API endpoint to get all reports (most recent first)"""
    printer_id = request.args.get('printer_id')
    limit = int(request.args.get('limit', 50))
    
    query = {}
    if printer_id:
        query['printer_id'] = printer_id
    
    reports = list(mongo.db.reports.find(query).sort('timestamp', -1).limit(limit))
    
    for report in reports:
        report['_id'] = str(report['_id'])
    
    return jsonify(reports)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        mongo.db.command('ping')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
