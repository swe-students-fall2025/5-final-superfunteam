import pytest
import db_schema
from unittest.mock import MagicMock, patch

def test_get_db_connection_returns_db():
    """Ensure get_db_connection returns the database object"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.get_database.return_value = mock_db

    with patch("db_schema.MongoClient", return_value=mock_client):
        db = db_schema.get_db_connection()
        assert db == mock_db
        mock_client.get_database.assert_called_once()

def test_create_collections_and_indexes():
    """Test that collections and indexes are created correctly (fixed)"""
    # Mock database
    mock_db = MagicMock()
    # Initially no collections exist
    mock_db.list_collection_names.return_value = []

    # Create mocks for printers and reports
    mock_db.printers = MagicMock()
    mock_db.reports = MagicMock()

    # Patch get_db_connection to return mock_db
    with patch("db_schema.get_db_connection", return_value=mock_db):
        db_schema.create_collections_and_indexes()

    # Check collection creation
    mock_db.create_collection.assert_any_call("printers")
    mock_db.create_collection.assert_any_call("reports")

    # Check printers indexes
    expected_printers_indexes = [
        ("name", db_schema.ASCENDING),
        ("location", db_schema.ASCENDING),
        ("building", db_schema.ASCENDING),
        ("created_at", db_schema.DESCENDING)
    ]
    for field, order in expected_printers_indexes:
        mock_db.printers.create_index.assert_any_call([(field, order)])

    # Check reports indexes
    mock_db.reports.create_index.assert_any_call([
        ("printer_id", db_schema.ASCENDING),
        ("timestamp", db_schema.DESCENDING)
    ])
    mock_db.reports.create_index.assert_any_call([("timestamp", db_schema.DESCENDING)])
    mock_db.reports.create_index.assert_any_call([("status", db_schema.ASCENDING)])


def test_create_collections_and_indexes_skips_existing_collections():
    """If collections exist, should not try to create them"""
    mock_db = MagicMock()
    mock_db.list_collection_names.return_value = ["printers", "reports"]

    with patch("db_schema.get_db_connection", return_value=mock_db):
        db_schema.create_collections_and_indexes()

    # create_collection should never be called
    mock_db.create_collection.assert_not_called()