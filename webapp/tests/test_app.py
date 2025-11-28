import pytest
from webapp.app import app
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
    with patch('webapp.app.mongo') as mock:
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

def test_delete_printer_api(client, mock_mongo):
    """Test DELETE /api/printers/<id> endpoint"""
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_mongo.db.printers.delete_one.return_value = mock_result
    
    response = client.delete('/api/printers/123')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_get_printer_not_found(client, mock_mongo):
    """Test GET /api/printers/<id> with non-existent printer"""
    mock_mongo.db.printers.find_one.return_value = None
    
    response = client.get('/api/printers/999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
