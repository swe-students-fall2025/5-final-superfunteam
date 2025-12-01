import pytest
from app import app
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_mongo():
    """Mock MongoDB connection"""
    with patch('app.mongo') as mock:
        yield mock

def test_index_route(client, mock_mongo):
    """Test the home page route"""
    mock_mongo.db.printers.find.return_value = []
    response = client.get('/')
    assert response.status_code == 200

def test_health_check(client, mock_mongo):
    """Test the health check endpoint"""
    mock_mongo.db.command.return_value = {'ok': 1}
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_get_printers_api(client, mock_mongo):
    """Test GET /api/printers endpoint"""
    mock_printers = [
        {'_id': '123', 'name': 'Test Printer', 'status': 'available'}
    ]
    mock_mongo.db.printers.find.return_value = mock_printers
    
    response = client.get('/api/printers')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_get_printers_api_empty(client, mock_mongo):
    """Test GET /api/printers endpoint when DB returns empty"""
    mock_mongo.db.printers.find.return_value = []
    
    response = client.get('/api/printers')
    assert response.status_code == 200  
    data = response.get_json()
    assert data == []  

def test_get_printers_api_empty(client, mock_mongo):
    """Test GET /api/printers endpoint when DB raises exception"""
    mock_mongo.db.printers.find.side_effect = Exception("DB failure")
    
    response = client.get('/api/printers')
    assert response.status_code == 500 
    data = response.get_json()
    assert "error" in data

def test_add_printer_api(client, mock_mongo):
    """Test POST /api/printers endpoint"""
    mock_result = MagicMock()
    mock_result.inserted_id = '123'
    mock_mongo.db.printers.insert_one.return_value = mock_result
    
    printer_data = {
        'name': 'Test Printer',
        'location': 'Bobst Library',
        'status': 'available',
        'paper_level': 80,
        'toner_level': 60
    }
    
    response = client.post('/api/printers', json=printer_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Test Printer'

def test_add_printer_api_fail(client, mock_mongo):
    """Test POST /api/printers endpoint with error exception"""
    mock_mongo.db.printers.insert_one.side_effect = Exception("DB failure")
    
    valid_data = {
        'name': 'Printer X',
        'location': 'Room 101',
        'status': 'available',
        'paper_level': 80,
        'toner_level': 60
    }
    
    response = client.post('/api/printers', json=valid_data)
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "DB failure"

def test_update_printer_api(client, mock_mongo):
    """Test PUT /api/printers/<id> endpoint"""
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_mongo.db.printers.update_one.return_value = mock_result
    
    update_data = {
        'status': 'busy',
        'paper_level': 50
    }
    
    response = client.put('/api/printers/123', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_update_printer_api_fail(client, mock_mongo):
    """Test PUT /api/printers/<id> endpoint failure cases"""
    bad_data = {
        'name': 'Updated Printer',  
        'location': 'Room 101'
    }

    response = client.put('/api/printers/507f1f77bcf86cd799439012', json=bad_data)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "No valid fields to update"

def test_update_printer_api_exception(client, mock_mongo):
    mock_mongo.db.printers.update_one.side_effect = Exception("DB failure")
    update_data = {
        'status': 'busy'  
    }

    response = client.put('/api/printers/507f1f77bcf86cd799439013', json=update_data)
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "DB failure"

def test_delete_printer_api(client, mock_mongo):
    """Test DELETE /api/printers/<id> endpoint"""
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_mongo.db.printers.delete_one.return_value = mock_result
    
    response = client.delete('/api/printers/123')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_delete_printer_api_not_found(client, mock_mongo):
    """Test DELETE /api/printers/<id> endpoint with printer not found"""
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    mock_mongo.db.printers.delete_one.return_value = mock_result

    response = client.delete('/api/printers/507f1f77bcf86cd799439012')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Printer not found"

def test_delete_printer_api_exception(client, mock_mongo):
    """Test DELETE /api/printers/<id> endpoint with exception rasied"""
    mock_mongo.db.printers.delete_one.side_effect = Exception("DB failure")

    response = client.delete('/api/printers/507f1f77bcf86cd799439013')
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "DB failure"

def test_get_printer_not_found(client, mock_mongo):
    """Test GET /api/printers/<id> with non-existent printer"""
    mock_mongo.db.printers.find_one.return_value = None
    
    response = client.get('/api/printers/999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
