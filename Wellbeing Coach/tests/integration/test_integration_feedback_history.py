import pytest 
import uuid
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
from app.db.db_connection import get_connection


client = TestClient(app)

@pytest.mark.integration
def test_post_feedback_success():
    conn = get_connection()
    cur = conn.cursor()
    
    activity_id = str(uuid.uuid4())
    mood = "stress"
    instructions = "Feeling overwhelmed is tough; here are three quick ways to recenter:\n""*   **Move:** Spend 5 minutes gently stretching your neck and shoulders to release physical tension.\n""*   **Breathe:** Practice 5 minutes of focused deep breathing (inhale 4, hold 4, exhale 4) to calm your nervous system.\n""*   **Ground:** Mindfully observe an everyday object for 5 minutes, noticing its textures and details."
    cur.execute("""
        INSERT INTO activities (activity_id,mood, instructions)
        VALUES (%s,%s,%s)
        """, (activity_id, mood, instructions)
    )
    
    conn.commit()
    
    payload = {
        "activity_id": activity_id,
        "rating": 5,
        "effective": True,
        "comment": "Very helpful"
    }
    
    response = client.post("/feedback", json=payload)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Feedback saved"
    
    cur.close()
    conn.close()
    
@pytest.mark.integration
def test_post_feedback_activity_not_found():

    payload = {
        "activity_id": str(uuid.uuid4()),
        "rating": 4,
        "effective": True,
        "comment": "Good"
    }

    response = client.post("/feedback", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity ID does not exist"

@pytest.mark.integration
def test_post_feedback_invalid_data():

    payload = {
        "activity_id": "asadasd",
        "rating": 4,
        "effective": True,
        "comment": "Good"
    }

    response = client.post("/feedback", json=payload)

    assert response.status_code == 422

@pytest.mark.integration
def test_post_feedback_activity_not_found():

    payload = {
        "activity_id": str(uuid.uuid4()),
        "rating": 4,
        "effective": True,
        "comment": "Good"
    }

    client.post("/feedback", json=payload)
    client.post("/feedback", json=payload)
    response = client.post("/feedback", json=payload)
    
    assert response.status_code == 429

@pytest.mark.integration
def test_get_history_success():
    response = client.get("/history")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)
    
    if len(data["history"]) > 0:
        item = data["history"][0]
        assert "user_input" in item
        assert "mood" in item
        assert "suggestions" in item

@pytest.mark.integration
@patch("app.routes.feedback_history.get_connection")
def test_get_history_not_found_error(mock_get_connection, api_client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_cursor.fetchall.return_value = []
    
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    
    response = api_client.get("/history")
    assert response.status_code == 404

@pytest.mark.integration        
def test_get_history_rate_limit():
    client.get("/history")
    client.get("/history")
    response = client.get("/history")

    assert response.status_code == 429