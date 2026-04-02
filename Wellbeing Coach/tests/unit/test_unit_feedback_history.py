import pytest
from fastapi.testclient import TestClient
from app.main import app
import time
from app.routes.feedback_history import get_history
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_post_feedback_success(mock_conn, api_client):
    
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("550e8400-e29b-41d4-a716-446655440000")
    
    payload = {
        "activity_id": "550e8400-e29b-41d4-a716-446655440000",
        "rating": 5,
        "effective": True,
        "comment": "very helpful"
    }
    
    response = api_client.post("/feedback", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Feedback saved"}
    
    
@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_post_feedback_invalid_data(mock_conn):
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("sssfsfs")
    
    payload = {
        "activity_id": "sssfsfs",
        "rating": "sds",
        "effective": "asfasf",
        "comment": 2
    }
    
    response = client.post("/feedback", json=payload)
    assert response.status_code == 422
    
    
@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_post_feedback_rate_limit_error(mock_conn):
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("550e8400-e29b-41d4-a716-446655440000")
    
    payload = {
        "activity_id": "550e8400-e29b-41d4-a716-446655440000",
        "rating": 5,
        "effective": True,
        "comment": "very helpful"
    }
    
    client.post("/feedback", json=payload)
    client.post("/feedback", json=payload)
    response = client.post("/feedback", json=payload)
    assert response.status_code == 429


@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_post_feedback_500_eroor(mock_conn, api_client):
    
    mock_conn.side_effect = Exception("Database connection falied")
    
    payload = {
        "activity_id": "550e8400-e29b-41d4-a716-446655440000",
        "rating": 5,
        "effective": True,
        "comment": "very helpful"
    }
    
    response = api_client.post("/feedback", json=payload)
    assert response.status_code == 500

@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_post_feedback_activity_not_found(mock_get_connection, api_client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = None
    
    payload = {
        "activity_id": "550e8400-e29b-41d4-a716-446655440000",
        "rating": 5,
        "effective": True,
        "comment": "very helpful"
    }
    
    response = api_client.post("/feedback", json=payload)
    assert response.status_code == 404

@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_get_history_success(mock_get_connection, api_client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_cursor.fetchall.return_value = {
        "history": [
            {
                "user_input": "I'm stuck in back-to-back meetings and feeling very overwhelmed.",
                "mood": "Overwhelmed",
                "suggestions": "Feeling overwhelmed is tough; here are three quick ways to recenter:\n"
                "*   **Move:** Spend 5 minutes gently stretching your neck and shoulders to release physical tension.\n"
                "*   **Breathe:** Practice 5 minutes of focused deep breathing (inhale 4, hold 4, exhale 4) to calm your nervous system.\n"
                "*   **Ground:** Mindfully observe an everyday object for 5 minutes, noticing its textures and details."
            }
        ]
    }
    
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    
    response = api_client.get("/history")
    assert response.status_code == 200

    
@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_get_history_rate_limit_exceeded(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_cursor.fetchall.return_value = {
        "history": [
            {
                "user_input": "I'm stuck in back-to-back meetings and feeling very overwhelmed.",
                "mood": "Overwhelmed",
                "suggestions": "Feeling overwhelmed is tough; here are three quick ways to recenter:\n"
                "*   **Move:** Spend 5 minutes gently stretching your neck and shoulders to release physical tension.\n"
                "*   **Breathe:** Practice 5 minutes of focused deep breathing (inhale 4, hold 4, exhale 4) to calm your nervous system.\n"
                "*   **Ground:** Mindfully observe an everyday object for 5 minutes, noticing its textures and details."
            }
        ]
    }
    
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    
    client.get("/history")
    client.get("/history")
    response = client.get("/history")
    assert response.status_code == 429


@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_get_history_500_error(mock_conn, api_client):
    
    mock_conn.side_effect = Exception("Database connection falied")
    
    response = api_client.get("/history")
    assert response.status_code == 500


@pytest.mark.unit
@patch("app.routes.feedback_history.get_connection")
def test_get_history_not_found_error(mock_get_connection, api_client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_cursor.fetchall.return_value = []
    
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    
    response = api_client.get("/history")
    assert response.status_code == 404