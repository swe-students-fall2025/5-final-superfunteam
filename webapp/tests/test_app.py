import pytest
from app import app
from unittest.mock import MagicMock, patch
from app import load_user, mongo, User
from bson import ObjectId
from datetime import datetime


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
    mock_mongo.db.study_spaces.find.return_value = []
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

def test_get_spaces_api(client, mock_mongo):
    """Test GET /api/spaces endpoint"""
    mock_spaces = [
        {'_id': '123', 'building': 'Bobst Library', 'sublocation': '2nd Floor'}
    ]
    mock_mongo.db.study_spaces.find.return_value = mock_spaces
    
    response = client.get('/api/spaces')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_get_spaces_api_empty(client, mock_mongo):
    """Test GET /api/spaces endpoint when DB returns empty"""
    mock_mongo.db.study_spaces.find.return_value = []
    
    response = client.get('/api/spaces')
    assert response.status_code == 200  
    data = response.get_json()
    assert data == []  

def test_get_spaces_api_exception(client, mock_mongo):
    """Test GET /api/spaces endpoint when DB raises exception"""
    mock_mongo.db.study_spaces.find.side_effect = Exception("DB failure")
    
    response = client.get('/api/spaces')
    assert response.status_code == 500 
    data = response.get_json()
    assert "error" in data

def test_add_space_api(client, mock_mongo):
    """Test POST /api/spaces endpoint"""
    mock_result = MagicMock()
    mock_result.inserted_id = '123'
    mock_mongo.db.study_spaces.insert_one.return_value = mock_result
    
    space_data = {
        'building': 'Bobst Library',
        'sublocation': '2nd Floor Study Area'
    }
    
    response = client.post('/api/spaces', json=space_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['building'] == 'Bobst Library'
    assert data['sublocation'] == '2nd Floor Study Area'

def test_add_space_api_fail(client, mock_mongo):
    """Test POST /api/spaces endpoint with error exception"""
    mock_mongo.db.study_spaces.insert_one.side_effect = Exception("DB failure")
    
    valid_data = {
        'building': 'Kimmel Center',
        'sublocation': 'Student Lounge'
    }
    
    response = client.post('/api/spaces', json=valid_data)
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "DB failure"

def test_add_space_api_with_ratings(client, mock_mongo):
    """Test POST /api/spaces endpoint with silence and crowdedness ratings"""
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId()
    mock_mongo.db.study_spaces.insert_one.return_value = mock_result
    
    # Mock review insert
    mock_review_result = MagicMock()
    mock_review_result.inserted_id = ObjectId()
    mock_mongo.db.reviews.insert_one.return_value = mock_review_result
    
    space_data = {
        'building': 'Bobst Library',
        'sublocation': '2nd Floor Study Area',
        'silence': 4,
        'crowdedness': 2
    }
    
    # Mock current_user for authenticated user
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.netid = 'test123'
        mock_user.email = 'test123@nyu.edu'
        
        response = client.post('/api/spaces', json=space_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['building'] == 'Bobst Library'
        assert data['sublocation'] == '2nd Floor Study Area'
        
        # Verify review was created
        mock_mongo.db.reviews.insert_one.assert_called_once()
        call_args = mock_mongo.db.reviews.insert_one.call_args[0][0]
        assert call_args['silence'] == 4
        assert call_args['crowdedness'] == 2
        assert call_args['rating'] == 3
        assert call_args['reported_by'] == 'test123'

def test_add_space_api_with_ratings_not_authenticated(client, mock_mongo):
    """Test POST /api/spaces with ratings but user not authenticated - should not create review"""
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId()
    mock_mongo.db.study_spaces.insert_one.return_value = mock_result
    
    space_data = {
        'building': 'Bobst Library',
        'sublocation': '2nd Floor Study Area',
        'silence': 4,
        'crowdedness': 2
    }
    
    # Mock current_user for unauthenticated user
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = False
        
        response = client.post('/api/spaces', json=space_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['building'] == 'Bobst Library'
        
        # Verify review was NOT created
        mock_mongo.db.reviews.insert_one.assert_not_called()

def test_update_space_api(client, mock_mongo):
    """Test PUT /api/spaces/<id> endpoint"""
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_mongo.db.study_spaces.update_one.return_value = mock_result
    
    update_data = {
        'building': 'Bobst Library',
        'sublocation': '3rd Floor'
    }
    
    response = client.put('/api/spaces/123', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_update_space_api_fail(client, mock_mongo):
    """Test PUT /api/spaces/<id> endpoint failure cases"""
    bad_data = {
        'invalid_field': 'value'
    }

    response = client.put('/api/spaces/507f1f77bcf86cd799439012', json=bad_data)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "No valid fields to update"

def test_update_space_api_exception(client, mock_mongo):
    mock_mongo.db.study_spaces.update_one.side_effect = Exception("DB failure")
    update_data = {
        'building': 'Updated Building'
    }

    response = client.put('/api/spaces/507f1f77bcf86cd799439013', json=update_data)
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "DB failure"

def test_delete_space_api(client, mock_mongo):
    """Test DELETE /api/spaces/<id> endpoint"""
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_mongo.db.study_spaces.delete_one.return_value = mock_result
    
    response = client.delete('/api/spaces/123')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_delete_space_api_not_found(client, mock_mongo):
    """Test DELETE /api/spaces/<id> endpoint with space not found"""
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    mock_mongo.db.study_spaces.delete_one.return_value = mock_result

    response = client.delete('/api/spaces/507f1f77bcf86cd799439012')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Study space not found"

def test_delete_space_api_exception(client, mock_mongo):
    """Test DELETE /api/spaces/<id> endpoint with exception raised"""
    mock_mongo.db.study_spaces.delete_one.side_effect = Exception("DB failure")

    response = client.delete('/api/spaces/507f1f77bcf86cd799439013')
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "DB failure"

def test_get_space_not_found(client, mock_mongo):
    """Test GET /api/spaces/<id> with non-existent space"""
    mock_mongo.db.study_spaces.find_one.return_value = None
    
    response = client.get('/api/spaces/999')
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

def test_submit_review_success(client, mock_mongo):
    """Test successful review submission"""
    space_id = str(ObjectId())
    
    # Mock space exists
    mock_mongo.db.study_spaces.find_one.return_value = {"_id": ObjectId(space_id)}
    
    # Mock insert result
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()
    mock_mongo.db.reviews.insert_one.return_value = mock_insert_result
    
    # Mock current_user
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        review_data = {
            "space_id": space_id,
            "rating": 4,
            "silence": 5,
            "crowdedness": 2,
            "review": "Great study space, very quiet!"
        }
        
        response = client.post('/api/reviews', json=review_data)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['space_id'] == space_id
        assert data['rating'] == 4
        assert data['silence'] == 5
        assert data['crowdedness'] == 2
        assert data['reported_by'] == 'test123'
        assert data['reporter_email'] == 'test123@nyu.edu'
        assert data['review'] == 'Great study space, very quiet!'
        assert '_id' in data
        assert 'timestamp' in data

def test_submit_review_missing_space_id(client, mock_mongo):
    """Test review submission without space_id"""
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reviews', json={
            "rating": 4,
            "silence": 5,
            "crowdedness": 2
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "space_id is required"

def test_submit_review_missing_ratings(client, mock_mongo):
    """Test review submission without required rating fields"""
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reviews', json={
            "space_id": str(ObjectId()),
            "rating": 4
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "rating, silence, and crowdedness are required" in data["error"]

def test_submit_review_space_not_found(client, mock_mongo):
    """Test review submission for non-existent space"""
    # Mock space doesn't exist
    mock_mongo.db.study_spaces.find_one.return_value = None
    
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reviews', json={
            "space_id": str(ObjectId()),
            "rating": 4,
            "silence": 5,
            "crowdedness": 2
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Study space not found"

def test_submit_review_invalid_rating_values(client, mock_mongo):
    """Test review submission with ratings out of 1-5 range"""
    space_id = str(ObjectId())
    mock_mongo.db.study_spaces.find_one.return_value = {"_id": ObjectId(space_id)}
    
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reviews', json={
            "space_id": space_id,
            "rating": 6,  # Invalid: > 5
            "silence": 5,
            "crowdedness": 2
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be between 1 and 5" in data["error"]

def test_get_reviews_success(client, mock_mongo):
    """Test GET /api/reviews endpoint returns all reviews"""
    mock_reviews = [
        {
            '_id': ObjectId(),
            'space_id': '123',
            'rating': 4,
            'silence': 5,
            'crowdedness': 2,
            'review': 'Great space!',
            'reported_by': 'test123',
            'reporter_email': 'test123@nyu.edu',
            'timestamp': '2024-01-01T12:00:00'
        },
        {
            '_id': ObjectId(),
            'space_id': '456',
            'rating': 3,
            'silence': 2,
            'crowdedness': 4,
            'review': 'Too crowded',
            'reported_by': 'user456',
            'reporter_email': 'user456@nyu.edu',
            'timestamp': '2024-01-01T11:00:00'
        }
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_reviews
    mock_mongo.db.reviews.find.return_value = mock_cursor
    
    response = client.get('/api/reviews')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['space_id'] == '123'
    assert data[1]['space_id'] == '456'

def test_get_reviews_filtered_by_space(client, mock_mongo):
    """Test GET /api/reviews with space_id filter"""
    space_id = '123'
    mock_reviews = [
        {
            '_id': ObjectId(),
            'space_id': space_id,
            'rating': 4,
            'silence': 5,
            'crowdedness': 2,
            'review': 'Great!',
            'reported_by': 'test123',
            'reporter_email': 'test123@nyu.edu',
            'timestamp': '2024-01-01T12:00:00'
        }
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_reviews
    mock_mongo.db.reviews.find.return_value = mock_cursor
    
    response = client.get(f'/api/reviews?space_id={space_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['space_id'] == space_id

def test_map_page_route(client, mock_mongo):
    """Test the /map route"""
    mock_spaces = [
        {
            '_id': ObjectId(),
            'building': 'Bobst Library',
            'sublocation': '2nd Floor Study Area'
        },
        {
            '_id': ObjectId(),
            'building': 'Kimmel Center',
            'sublocation': 'Student Lounge'
        }
    ]
    mock_mongo.db.study_spaces.find.return_value = mock_spaces
    
    response = client.get('/map')
    assert response.status_code == 200
    # Check that the response contains HTML
    assert b'Study Spaces' in response.data

def test_map_page_empty(client, mock_mongo):
    """Test the /map route with no spaces"""
    mock_mongo.db.study_spaces.find.return_value = []
    
    response = client.get('/map')
    assert response.status_code == 200
    # Check that the response contains the no spaces message
    assert b'No study spaces found' in response.data or b'Study Spaces' in response.data

def test_add_space_page(client):
    """Test the /add-space route"""
    response = client.get('/add-space')
    assert response.status_code == 200
    assert b'Add New Study Space' in response.data

def test_get_current_user(client, mock_mongo):
    """Test GET /api/user endpoint"""
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.email = 'test@nyu.edu'
        mock_user.netid = 'test123'
        
        response = client.get('/api/user')
        assert response.status_code == 200
        data = response.get_json()
        assert data['email'] == 'test@nyu.edu'
        assert data['netid'] == 'test123'

def test_validate_nyu_email():
    """Test validate_nyu_email helper function"""
    from app import validate_nyu_email
    
    assert validate_nyu_email('test@nyu.edu') == True
    assert validate_nyu_email('user@nyu.edu') == True
    assert validate_nyu_email('test@gmail.com') == False
    assert validate_nyu_email('invalid') == False
    assert validate_nyu_email('test@nyu.com') == False

def test_index_route_with_reviews(client, mock_mongo):
    """Test index route with spaces that have reviews"""
    mock_space = {
        '_id': ObjectId(),
        'building': 'Bobst Library',
        'sublocation': '2nd Floor'
    }
    mock_mongo.db.study_spaces.find.return_value = [mock_space]
    
    mock_reviews = [
        {
            '_id': ObjectId(),
            'space_id': str(mock_space['_id']),
            'rating': 4,
            'silence': 5,
            'crowdedness': 2,
            'review': 'Great space!',
            'reported_by': 'test123',
            'timestamp': datetime.utcnow()
        },
        {
            '_id': ObjectId(),
            'space_id': str(mock_space['_id']),
            'rating': 5,
            'silence': 4,
            'crowdedness': 3,
            'review': 'Excellent!',
            'reported_by': 'test456',
            'timestamp': datetime.utcnow()
        }
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_reviews
    mock_mongo.db.reviews.find.return_value = mock_cursor
    
    response = client.get('/')
    assert response.status_code == 200
    assert b'Bobst Library' in response.data

def test_add_space_invalid_ratings(client, mock_mongo):
    """Test add_space with invalid rating values"""
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId()
    mock_mongo.db.study_spaces.insert_one.return_value = mock_result
    
    space_data = {
        'building': 'Bobst Library',
        'sublocation': '2nd Floor',
        'silence': 6,  # Invalid: > 5
        'crowdedness': 2
    }
    
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.netid = 'test123'
        mock_user.email = 'test123@nyu.edu'
        
        response = client.post('/api/spaces', json=space_data)
        assert response.status_code == 201
        # Space should be created but review should not (invalid ratings)
        mock_mongo.db.reviews.insert_one.assert_not_called()

def test_add_space_invalid_rating_type(client, mock_mongo):
    """Test add_space with invalid rating type"""
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId()
    mock_mongo.db.study_spaces.insert_one.return_value = mock_result
    
    space_data = {
        'building': 'Bobst Library',
        'sublocation': '2nd Floor',
        'silence': 'invalid',  # Invalid type
        'crowdedness': 2
    }
    
    with patch('app.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.netid = 'test123'
        mock_user.email = 'test123@nyu.edu'
        
        response = client.post('/api/spaces', json=space_data)
        assert response.status_code == 201
        # Review should not be created due to invalid type
        mock_mongo.db.reviews.insert_one.assert_not_called()

def test_update_space_no_valid_fields(client, mock_mongo):
    """Test update_space with no valid fields to update"""
    update_data = {
        'invalid_field': 'value'
    }
    
    response = client.put('/api/spaces/507f1f77bcf86cd799439012', json=update_data)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "No valid fields to update"

def test_get_space_with_reviews(client, mock_mongo):
    """Test GET /api/spaces/<id> with reviews"""
    space_id = str(ObjectId())
    mock_space = {
        '_id': ObjectId(space_id),
        'building': 'Bobst Library',
        'sublocation': '2nd Floor'
    }
    mock_mongo.db.study_spaces.find_one.return_value = mock_space
    
    mock_reviews = [
        {
            '_id': ObjectId(),
            'space_id': space_id,
            'rating': 4,
            'silence': 5,
            'crowdedness': 2,
            'review': 'Great!',
            'reported_by': 'test123',
            'timestamp': datetime.utcnow()
        }
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_reviews
    mock_mongo.db.reviews.find.return_value = mock_cursor
    
    response = client.get(f'/api/spaces/{space_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['building'] == 'Bobst Library'
    assert 'reviews' in data
    assert len(data['reviews']) == 1

def test_get_space_with_no_reviews(client, mock_mongo):
    """Test GET /api/spaces/<id> with no reviews"""
    space_id = str(ObjectId())
    mock_space = {
        '_id': ObjectId(space_id),
        'building': 'Bobst Library',
        'sublocation': '2nd Floor'
    }
    mock_mongo.db.study_spaces.find_one.return_value = mock_space
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = []
    mock_mongo.db.reviews.find.return_value = mock_cursor
    
    response = client.get(f'/api/spaces/{space_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['building'] == 'Bobst Library'
    assert data['review_count'] == 0
    assert data['avg_rating'] == 0

def test_update_space_not_found(client, mock_mongo):
    """Test update_space when space is not found"""
    mock_result = MagicMock()
    mock_result.matched_count = 0
    mock_mongo.db.study_spaces.update_one.return_value = mock_result
    
    update_data = {
        'building': 'Updated Building'
    }
    
    response = client.put('/api/spaces/507f1f77bcf86cd799439012', json=update_data)
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Study space not found"

def test_submit_review_invalid_rating_type(client, mock_mongo):
    """Test review submission with invalid rating type"""
    space_id = str(ObjectId())
    mock_mongo.db.study_spaces.find_one.return_value = {"_id": ObjectId(space_id)}
    
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reviews', json={
            "space_id": space_id,
            "rating": "invalid",  # Invalid type
            "silence": 5,
            "crowdedness": 2
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

def test_submit_review_rating_zero(client, mock_mongo):
    """Test review submission with rating of 0 (below valid range)"""
    space_id = str(ObjectId())
    mock_mongo.db.study_spaces.find_one.return_value = {"_id": ObjectId(space_id)}
    
    with patch('app.current_user') as mock_current_user:
        mock_current_user.netid = "test123"
        mock_current_user.email = "test123@nyu.edu"
        
        response = client.post('/api/reviews', json={
            "space_id": space_id,
            "rating": 0,  # Invalid: < 1
            "silence": 5,
            "crowdedness": 2
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "must be between 1 and 5" in data["error"]
