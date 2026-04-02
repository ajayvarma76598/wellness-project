import pytest
from unittest.mock import patch, MagicMock
from app.db.db_connection import get_connection, create_tables

@pytest.mark.unit
@patch("app.db.db_connection.psycopg2.connect")
def test_get_Connection_successs(mock_connect):
    
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    conn = get_connection()
    
    assert conn == mock_conn
    mock_connect.assert_called_once()
    
@pytest.mark.unit
@patch("app.db.db_connection.psycopg2.connect")
def test_get_Connection_failure(mock_connect):
    
    
    mock_connect.side_effect = Exception("DB connection error")
    
    with pytest.raises(Exception):
        get_connection()
        
@pytest.mark.unit
@patch("app.db.db_connection.get_connection")
def test_create_tables(mock_get_connection):

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    create_tables()

    assert mock_cursor.execute.call_count == 4

    mock_conn.commit.assert_called_once()

    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

@pytest.mark.unit
@patch("app.db.db_connection.get_connection")
def test_create_tables_exception(mock_get_connection):

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_cursor.execute.side_effect = Exception("SQL error")

    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    with pytest.raises(Exception):
        create_tables()