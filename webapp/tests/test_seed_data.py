import pytest
import seed_data
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime


def test_get_db_connection():
    """Test get_db_connection function"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    database_name = "proj4"
    mock_client.__getitem__.return_value = mock_db

    with patch("seed_data.MongoClient", return_value=mock_client):
        with patch("seed_data.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": None,
                "MONGODB_HOST": "localhost",
                "MONGODB_PORT": "27017",
                "MONGODB_DATABASE": database_name
            }.get(key, default)
            
            db = seed_data.get_db_connection()
            assert db == mock_db
            mock_client.__getitem__.assert_called_once_with(database_name)


def test_get_db_connection_with_mongo_uri():
    """Test get_db_connection when MONGO_URI is provided"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    database_name = "proj4"
    mock_client.__getitem__.return_value = mock_db

    with patch("seed_data.MongoClient", return_value=mock_client):
        with patch("seed_data.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": "mongodb://localhost:27017/",
                "MONGODB_DATABASE": database_name
            }.get(key, default)
            
            db = seed_data.get_db_connection()
            assert db == mock_db


def test_get_db_connection_exception():
    """Test get_db_connection handles exceptions"""
    with patch("seed_data.MongoClient", side_effect=Exception("Connection failed")):
        with patch("seed_data.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": None,
                "MONGODB_HOST": "localhost",
                "MONGODB_PORT": "27017",
                "MONGODB_DATABASE": "proj4"
            }.get(key, default)
            
            with pytest.raises(Exception) as excinfo:
                seed_data.get_db_connection()
            assert "Connection failed" in str(excinfo.value)


def test_seed_study_spaces_success():
    """Test successful seeding of study spaces"""
    mock_db = MagicMock()
    mock_db.study_spaces.count_documents.return_value = 0
    mock_result = MagicMock()
    mock_result.inserted_ids = [ObjectId() for _ in range(12)]
    mock_db.study_spaces.insert_many.return_value = mock_result
    mock_db.reviews.insert_many.return_value = MagicMock()

    with patch("seed_data.get_db_connection", return_value=mock_db):
        seed_data.seed_study_spaces()
        
        mock_db.study_spaces.insert_many.assert_called_once()
        call_args = mock_db.study_spaces.insert_many.call_args[0][0]
        assert len(call_args) == 12
        assert call_args[0]["building"] == "Bobst Library"
        
        # Verify reviews were inserted
        mock_db.reviews.insert_many.assert_called_once()


def test_seed_study_spaces_existing_data():
    """Test seeding when data already exists"""
    mock_db = MagicMock()
    mock_db.study_spaces.count_documents.return_value = 5

    with patch("seed_data.get_db_connection", return_value=mock_db):
        seed_data.seed_study_spaces()
        
        # Should not insert if data exists
        mock_db.study_spaces.insert_many.assert_not_called()


def test_seed_study_spaces_no_reviews():
    """Test seeding when no spaces are inserted (no reviews should be added)"""
    mock_db = MagicMock()
    mock_db.study_spaces.count_documents.return_value = 0
    mock_result = MagicMock()
    mock_result.inserted_ids = []  # No spaces inserted
    mock_db.study_spaces.insert_many.return_value = mock_result

    with patch("seed_data.get_db_connection", return_value=mock_db):
        seed_data.seed_study_spaces()
        
        mock_db.study_spaces.insert_many.assert_called_once()
        # No reviews should be inserted if no spaces were created
        mock_db.reviews.insert_many.assert_not_called()

