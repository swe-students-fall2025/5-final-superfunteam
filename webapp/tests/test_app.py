import pytest
from app import app
from unittest.mock import MagicMock, patch
from app import load_user, mongo, User
from bson import ObjectId


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config["LOGIN_DISABLED"] = True
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

def test_load_user_found():
    mock_user_data = {
        "email": "test@nyu.edu",
        "_id": "abc123"
    }

    # Patch the 'users' collection on mongo.db
    with patch.object(mongo.db, "users", create=True) as mock_users:
        mock_users.find_one.return_value = mock_user_data

        user_obj = load_user("test@nyu.edu")

        mock_users.find_one.assert_called_once_with({"email": "test@nyu.edu"})
        assert user_obj.email == "test@nyu.edu"
        assert user_obj.id == "abc123"

def test_load_user_not_found():
    """Test load_user returns None when user does not exist"""
    with patch.object(mongo.db, "users", create=True) as mock_users:
        mock_users.find_one.return_value = None

        user_obj = load_user("missing@nyu.edu")

        mock_users.find_one.assert_called_once_with({"email": "missing@nyu.edu"})
        assert user_obj is None


def test_load_user_db_exception():
    """Test load_user handles DB exceptions gracefully"""
    with patch.object(mongo.db, "users", create=True) as mock_users:
        mock_users.find_one.side_effect = Exception("DB error")

        with pytest.raises(Exception) as excinfo:
            load_user("error@nyu.edu")

        assert "DB error" in str(excinfo.value)
        mock_users.find_one.assert_called_once_with({"email": "error@nyu.edu"})

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

def test_login_success(client, mock_mongo):
    pw_hash = b"$2b$12$saltsaltsaltsaltsaltsaltpwhashed"
    mock_mongo.db.users.find_one.return_value = {
        "email": "test@nyu.edu",
        "password_hash": pw_hash.decode("utf-8"),
        "netid": "test",
        "_id": "abc123" 
    }

    with patch('app.checkpw', return_value=True):
        response = client.post("/api/login", json={
            "email": "test@nyu.edu",
            "password": "securepass"
        })

    assert response.status_code == 200

def test_login_wrong_password(client, mock_mongo):
    """Test login with incorrect password"""
    mock_mongo.db.users.find_one.return_value = {
        "email": "test@nyu.edu",
        "password_hash": b"$2b$12$saltsaltsaltsaltsaltsaltpwhashed".decode("utf-8"),
        "netid": "test",
        "_id": "abc123" 
    }

    with patch('app.checkpw', return_value=False):
        response = client.post("/api/login", json={
            "email": "test@nyu.edu",
            "password": "wrongpassword"
        })

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid email or password"

def test_login_user_not_found(client, mock_mongo):
    """Test login with an email that does not exist"""
    mock_mongo.db.users.find_one.return_value = None 

    response = client.post("/api/login", json={
        "email": "nonexistent@nyu.edu",
        "password": "somepassword"
    })

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid email or password"

def test_login_missing_fields(client, mock_mongo):
    """Test login with missing email or password"""
    response = client.post("/api/login", json={
        "email": "",
        "password": ""
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Email and password are required"

def test_register_success(client, mock_mongo):
    """Test successful user registration"""
    # No existing user
    mock_mongo.db.users.find_one.return_value = None

    # Mock insert_one to return a fake inserted_id
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "user123"
    mock_mongo.db.users.insert_one.return_value = mock_insert_result

    response = client.post("/api/register", json={
        "email": "newuser@nyu.edu",
        "password": "strongpassword"
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User registered successfully"
    assert data["user"]["email"] == "newuser@nyu.edu"
    assert data["user"]["_id"] == "user123"

def test_register_invalid_email(client, mock_mongo):
    """Test registration with non-NYU email"""
    response = client.post("/api/register", json={
        "email": "notnyu@gmail.com",
        "password": "strongpassword"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "NYU email" in data["error"]

def test_register_short_password(client, mock_mongo):
    """Test registration with password shorter than 6 characters"""
    response = client.post("/api/register", json={
        "email": "test@nyu.edu",
        "password": "123"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "at least 6 characters" in data["error"]

def test_register_duplicate_email(client, mock_mongo):
    """Test registration when email is already registered"""
    # Simulate existing user in database
    mock_mongo.db.users.find_one.return_value = {
        "email": "existing@nyu.edu",
        "password_hash": "hash",
        "_id": "existing123"
    }

    response = client.post("/api/register", json={
        "email": "existing@nyu.edu",
        "password": "anotherpassword"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "already registered" in data["error"]

def test_submit_report_success(client, mock_mongo):
    """Test successful report submission"""
    printer_id = str(ObjectId())
    
    # Mock printer exists
    mock_mongo.db.printers.find_one.return_value = {"_id": ObjectId(printer_id)}
    
    # Mock insert result
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()
    mock_mongo.db.reports.insert_one.return_value = mock_insert_result
    
    # Mock current_user
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        report_data = {
            "printer_id": printer_id,
            "status": "available",
            "paper_level": 80,
            "toner_level": 60,
            "comments": "Printer is working well"
        }
        
        response = client.post('/api/reports', json=report_data)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['printer_id'] == printer_id
        assert data['status'] == 'available'
        assert data['reported_by'] == 'test123'
        assert data['reporter_email'] == 'test123@nyu.edu'
        assert data['paper_level'] == 80
        assert data['toner_level'] == 60
        assert data['comments'] == 'Printer is working well'
        assert '_id' in data
        assert 'timestamp' in data

def test_submit_report_missing_printer_id(client, mock_mongo):
    """Test report submission without printer_id"""
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reports', json={
            "status": "available"
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "printer_id and status are required"

def test_submit_report_missing_status(client, mock_mongo):
    """Test report submission without status"""
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reports', json={
            "printer_id": str(ObjectId())
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "printer_id and status are required"

def test_submit_report_printer_not_found(client, mock_mongo):
    """Test report submission for non-existent printer"""
    # Mock printer doesn't exist
    mock_mongo.db.printers.find_one.return_value = None
    
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reports', json={
            "printer_id": str(ObjectId()),
            "status": "available"
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Printer not found"

def test_get_reports_success(client, mock_mongo):
    """Test GET /api/reports endpoint returns all reports"""
    mock_reports = [
        {
            '_id': ObjectId(),
            'printer_id': '123',
            'status': 'available',
            'reported_by': 'test123',
            'reporter_email': 'test123@nyu.edu',
            'paper_level': 80,
            'toner_level': 60,
            'comments': 'Working well',
            'timestamp': '2024-01-01T12:00:00'
        },
        {
            '_id': ObjectId(),
            'printer_id': '456',
            'status': 'busy',
            'reported_by': 'user456',
            'reporter_email': 'user456@nyu.edu',
            'paper_level': 50,
            'toner_level': 40,
            'comments': 'In use',
            'timestamp': '2024-01-01T11:00:00'
        }
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_reports
    mock_mongo.db.reports.find.return_value = mock_cursor
    
    response = client.get('/api/reports')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['printer_id'] == '123'
    assert data[1]['printer_id'] == '456'