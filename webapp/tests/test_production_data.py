import pytest
import production_data
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from bson import ObjectId


def test_get_db_connection():
    """Test get_db_connection function"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    database_name = "proj4"
    mock_client.__getitem__.return_value = mock_db

    with patch("production_data.MongoClient", return_value=mock_client):
        with patch("production_data.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": None,
                "MONGODB_HOST": "localhost",
                "MONGODB_PORT": "27017",
                "MONGODB_DATABASE": database_name
            }.get(key, default)
            
            db = production_data.get_db_connection()
            assert db == mock_db
            mock_client.__getitem__.assert_called_once_with(database_name)


def test_get_db_connection_with_mongo_uri():
    """Test get_db_connection when MONGO_URI is provided"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    database_name = "proj4"
    mock_client.__getitem__.return_value = mock_db

    with patch("production_data.MongoClient", return_value=mock_client):
        with patch("production_data.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": "mongodb://localhost:27017/",
                "MONGODB_DATABASE": database_name
            }.get(key, default)
            
            db = production_data.get_db_connection()
            assert db == mock_db


def test_get_db_connection_exception():
    """Test get_db_connection handles exceptions"""
    with patch("production_data.MongoClient", side_effect=Exception("Connection failed")):
        with patch("production_data.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "MONGO_URI": None,
                "MONGODB_HOST": "localhost",
                "MONGODB_PORT": "27017",
                "MONGODB_DATABASE": "proj4"
            }.get(key, default)
            
            with pytest.raises(Exception) as excinfo:
                production_data.get_db_connection()
            assert "Connection failed" in str(excinfo.value)


def test_insert_production_printers_success():
    """Test successful insertion of production printers"""
    mock_db = MagicMock()
    mock_db.printers.count_documents.return_value = 0
    mock_result = MagicMock()
    mock_result.inserted_ids = [ObjectId() for _ in range(3)]
    mock_db.printers.insert_many.return_value = mock_result

    with patch("production_data.get_db_connection", return_value=mock_db):
        with patch("builtins.input", return_value="yes"):
            production_data.insert_production_printers()
            
            mock_db.printers.insert_many.assert_called_once()
            call_args = mock_db.printers.insert_many.call_args[0][0]
            assert len(call_args) == 3
            assert call_args[0]["building"] == "Bobst Library"


def test_insert_production_printers_existing_data():
    """Test insertion when data already exists"""
    mock_db = MagicMock()
    mock_db.printers.count_documents.return_value = 5
    mock_result = MagicMock()
    mock_result.inserted_ids = [ObjectId() for _ in range(3)]
    mock_db.printers.insert_many.return_value = mock_result

    with patch("production_data.get_db_connection", return_value=mock_db):
        with patch("builtins.input", return_value="yes"):
            production_data.insert_production_printers()
            
            mock_db.printers.delete_many.assert_called()
            mock_db.printers.insert_many.assert_called_once()


def test_insert_production_printers_cancelled():
    """Test insertion when user cancels"""
    mock_db = MagicMock()
    mock_db.printers.count_documents.return_value = 5

    with patch("production_data.get_db_connection", return_value=mock_db):
        with patch("builtins.input", return_value="no"):
            production_data.insert_production_printers()
            
            mock_db.printers.insert_many.assert_not_called()


def test_insert_production_printers_insufficient_data():
    """Test insertion with insufficient data (less than 5 printers)"""
    mock_db = MagicMock()
    mock_db.printers.count_documents.return_value = 0

    with patch("production_data.get_db_connection", return_value=mock_db):
        with patch("builtins.input", return_value="no"):
            production_data.insert_production_printers()
            
            mock_db.printers.insert_many.assert_not_called()

