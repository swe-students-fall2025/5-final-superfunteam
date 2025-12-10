import pytest
import db_schema
from unittest.mock import MagicMock, patch

def test_get_db_connection_returns_db():
    """Ensure get_db_connection returns the database object"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    database_name = "proj4"
    mock_client.__getitem__.return_value = mock_db

    with patch("db_schema.MongoClient", return_value=mock_client):
        with patch("db_schema.os.getenv") as mock_getenv:
            # Mock environment variables - no MONGO_URI, use individual components
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": None,
                "MONGODB_HOST": "localhost",
                "MONGODB_PORT": "27017",
                "MONGODB_DATABASE": database_name
            }.get(key, default)
            
            db = db_schema.get_db_connection()
            assert db == mock_db
            mock_client.__getitem__.assert_called_once_with(database_name)

def test_get_db_connection_with_mongo_uri():
    """Test get_db_connection when MONGO_URI is provided"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    database_name = "proj4"
    mock_client.__getitem__.return_value = mock_db

    with patch("db_schema.MongoClient", return_value=mock_client):
        with patch("db_schema.os.getenv") as mock_getenv:
            # Mock environment variables - MONGO_URI provided
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": "mongodb://localhost:27017/",
                "MONGODB_DATABASE": database_name
            }.get(key, default)
            
            db = db_schema.get_db_connection()
            assert db == mock_db
            mock_client.__getitem__.assert_called_once_with(database_name)

def test_create_collections_and_indexes():
    """Test that collections and indexes are created correctly"""
    # Mock database
    mock_db = MagicMock()
    # Initially no collections exist
    mock_db.list_collection_names.return_value = []

    # Create mocks for study_spaces and reviews
    mock_db.study_spaces = MagicMock()
    mock_db.reviews = MagicMock()

    # Patch get_db_connection to return mock_db
    with patch("db_schema.get_db_connection", return_value=mock_db):
        db_schema.create_collections_and_indexes()

    # Check collection creation
    mock_db.create_collection.assert_any_call("study_spaces")
    mock_db.create_collection.assert_any_call("reviews")

    # Check study_spaces indexes
    expected_study_spaces_indexes = [
        ("building", db_schema.ASCENDING),
        ("sublocation", db_schema.ASCENDING),
        ("created_at", db_schema.DESCENDING)
    ]
    for field, order in expected_study_spaces_indexes:
        mock_db.study_spaces.create_index.assert_any_call([(field, order)])

    # Check reviews indexes
    mock_db.reviews.create_index.assert_any_call([
        ("space_id", db_schema.ASCENDING),
        ("timestamp", db_schema.DESCENDING)
    ])
    mock_db.reviews.create_index.assert_any_call([("timestamp", db_schema.DESCENDING)])
    mock_db.reviews.create_index.assert_any_call([("rating", db_schema.ASCENDING)])


def test_create_collections_and_indexes_skips_existing_collections():
    """If collections exist, should not try to create them"""
    mock_db = MagicMock()
    # Include all collections that db_schema creates (including review_votes)
    mock_db.list_collection_names.return_value = ["study_spaces", "reviews", "study_space_requests", "review_votes"]
    
    # Mock the collection objects for index creation
    mock_db.study_spaces = MagicMock()
    mock_db.reviews = MagicMock()
    mock_db.study_space_requests = MagicMock()
    mock_db.review_votes = MagicMock()

    with patch("db_schema.get_db_connection", return_value=mock_db):
        db_schema.create_collections_and_indexes()

    # create_collection should never be called since all collections exist
    mock_db.create_collection.assert_not_called()
