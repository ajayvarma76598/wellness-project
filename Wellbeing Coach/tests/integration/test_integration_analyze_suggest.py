"""Integration tests for the Wellbeing Coach analyze-mood and suggest-activity endpoints.

These tests validate the full workflow of emotional state analysis and activity suggestion
using real LLM calls and database interactions.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

# Rate limit configuration - endpoints are limited to 2 requests per minute
RATE_LIMIT_PER_MINUTE = 2
#client = TestClient(app)

@pytest.mark.integration
def test_suggest_activity_fails_without_mood(api_client):
    """
    Ensures 400 is returned if no mood has been analyzed yet.
    Note: Run this test alone or ensure state is cleared to avoid getting a 200 
    from a previous test's success.
    """
    response = api_client.get("/suggest-activity")
    assert response.status_code == 400
    assert "analyze-mood first!" in response.json()["detail"]

@pytest.mark.integration
def test_analyze_mood_invalid_request(api_client):
    """Test API rejects missing user_input field"""
    #time.sleep(65)
    response = api_client.post("/analyze-mood", json={"wrong_key": "hello"})
    assert response.status_code == 422

# @pytest.mark.integration
# def test_analyze_mood_success(api_client):
#     """Test the mood analysis endpoint with a real LLM call"""
#     request_data = {"user_input": "I am feeling very productive and happy today!"}
#     response = api_client.post("/analyze-mood", json=request_data)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert "emotion" in data
#     assert isinstance(data["emotion"], str)
#     # The LLM should return a one-word emotion as per the prompt
#     assert len(data["emotion"].split()) <= 2 

# @pytest.mark.integration
# def test_suggest_activity_success_stream(api_client):
#     """Test streaming activity suggestion after a mood is set"""
#     # Note: This relies on the state from the previous test or needs its own setup
#     # because capture_user_emotion is a local variable in the router factory.
    
#     # 1. Set the mood first
#     api_client.post("/analyze-mood", json={"user_input": "I feel stressed"})
    
#     # 2. Get the suggestion
#     with api_client.stream("GET", "/suggest-activity") as response:
#         assert response.status_code == 200
#         assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"
        
#         chunks = []
#         for chunk in response.iter_text():
#             if chunk:
#                 chunks.append(chunk)
        
#         full_text = "".join(chunks)
#         assert "Activity ID:" in full_text
#         assert len(full_text) > 10

# @pytest.mark.integration
# def test_full_flow_integration(api_client):
#     """Test the dependency: Mood -> Suggestion"""
#     # Step 1: Set the mood
#     #time.sleep(65)
#     api_client.post("/analyze-mood", json={"user_input": "I feel great"})
    
#     # Step 2: Get the suggestion stream
#     with api_client.stream("GET", "/suggest-activity") as response:
#         assert response.status_code == 429
