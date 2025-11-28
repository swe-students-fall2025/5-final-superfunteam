from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nyu_printers")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

mongo = PyMongo(app)

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
    printer = mongo.db.printers.find_one({'_id': ObjectId(printer_id)})
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
        result = mongo.db.printers.update_one(
            {'_id': ObjectId(printer_id)},
            {'$set': update_data}
        )
        
        if result.matched_count:
            return jsonify({'message': 'Printer updated successfully'})
        return jsonify({'error': 'Printer not found'}), 404
    
    return jsonify({'error': 'No valid fields to update'}), 400

@app.route('/api/printers/<printer_id>', methods=['DELETE'])
def delete_printer(printer_id):
    """API endpoint to delete a printer"""
    result = mongo.db.printers.delete_one({'_id': ObjectId(printer_id)})
    if result.deleted_count:
        return jsonify({'message': 'Printer deleted successfully'})
    return jsonify({'error': 'Printer not found'}), 404

@app.route('/api/reports', methods=['POST'])
def submit_report():
    """API endpoint for users to submit printer status reports"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('printer_id') or not data.get('status'):
        return jsonify({'error': 'printer_id and status are required'}), 400
    
    # Verify printer exists
    printer = mongo.db.printers.find_one({'_id': ObjectId(data['printer_id'])})
    if not printer:
        return jsonify({'error': 'Printer not found'}), 404
    
    report = {
        'printer_id': data['printer_id'],
        'status': data['status'],  # available, busy, offline, out_of_paper, out_of_toner
        'paper_level': data.get('paper_level', 0),
        'toner_level': data.get('toner_level', 0),
        'reported_by': data.get('reported_by', 'Anonymous'),
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
