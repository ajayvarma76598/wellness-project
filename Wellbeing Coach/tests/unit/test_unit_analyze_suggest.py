from openai import RateLimitError
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock

def _clear_suggest_state(api_client):
    """Clear the internal state captured by the /suggest-activity endpoint between tests."""
    for route in api_client.app.router.routes:
        if getattr(route, "path", None) == "/suggest-activity":
            endpoint = getattr(route, "endpoint", None)
            if endpoint is None or endpoint.__closure__ is None:
                continue
            for cell in endpoint.__closure__:
                if isinstance(cell.cell_contents, dict) and "emotion" in cell.cell_contents:
                    cell.cell_contents.clear()
                    return

@pytest.mark.unit
def test_health_check(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "llm-query-api"
    assert data["version"] == "1.0.0"

@pytest.mark.unit
@patch('app.main.client.chat.completions.create')
def test_analyze_mood_success(mock_generate_response, api_client):
    mock_generate_response.return_value.choices[0].message.content = "anxious"
    response = api_client.post("/analyze-mood", json={"user_input": "I'm feeling overwhelmed with work and family responsibilities."})
    assert response.status_code == 200
    data = response.json()
    assert data["emotion"] == "anxious"

    mock_generate_response.assert_called_once()
    call_arguments = mock_generate_response.call_args
    assert call_arguments.kwargs['messages'][0]['content'].strip() == "You are an expert Wellbeing Coach. Analyze the following user input to identify their emotional state.\n            User Input: \"I'm feeling overwhelmed with work and family responsibilities.\"\n            Determine the emotion state in one word (e.g., happy, sad, anxious, etc.)  ".strip()

@pytest.mark.unit
def test_analyze_mood_with_empty_prompt(api_client):
    response = api_client.post("/analyze-mood", json={"user_input": ""})
    assert response.status_code == 422 
    data = response.json()
    assert data["detail"][0]["msg"] == "String should have at least 20 characters"

@pytest.mark.unit
def test_analyze_mood_with_invalid_input(api_client):
    response = api_client.post("/analyze-mood", json={"user_input": 1234})
    assert response.status_code == 422 
    data = response.json()
    assert data["detail"][0]["msg"] == "Input should be a valid string"

@pytest.mark.unit
@patch('app.main.client.chat.completions.create')
def test_analyze_mood_rate_limit_error(mock_generate_response, api_client):
    mock_generate_response.side_effect = RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(),
        body={'error': 'Too many requests'}
    )

    response = api_client.post("/analyze-mood", json={"user_input": "I'm feeling overwhelmed with work and family responsibilities."})

    assert response.status_code == 429
    detail = response.json()["detail"]
    
    if isinstance(detail, dict):
        assert "API rate limit exceeded" in detail.get("error", "")
    else:
        assert "rate" in detail.lower()

@pytest.mark.unit
def test_suggest_activity_database_insertion_success(api_client):
    """Verifies that the activity is correctly saved to the DB after streaming."""
    _clear_suggest_state(api_client)

    # 1. Establish mood
    with patch('app.main.client.chat.completions.create') as mock_mood:
        mock_mood.return_value.choices[0].message.content = "stressed"
        api_client.post("/analyze-mood", json={"user_input": "Work is too much."})

    # 2. Mock AI Stream and Database
    with patch('app.main.client.chat.completions.create') as mock_suggest, \
         patch('app.routes.analyze_suggest.get_connection') as mock_db:
        
        # Mock streaming chunks
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "Practice deep breathing."
        mock_suggest.return_value = [chunk]

        # Mock DB cursor to return a dummy activity_id
        mock_conn = mock_db.return_value
        mock_cur = mock_conn.cursor.return_value
        mock_cur.fetchone.return_value = [123]

        response = api_client.get("/suggest-activity")
        
        assert response.status_code == 200
        assert "Activity ID: 123" in response.text
        # Ensure the DB insert was called with the correct emotion
        mock_cur.execute.assert_called()

@pytest.mark.unit
def test_suggest_activity_prompt_structure(api_client):
    """Ensures the prompt sent to the AI contains the required wellbeing coach role."""
    _clear_suggest_state(api_client)
    
    with patch('app.main.client.chat.completions.create') as mock_mood:
        mock_mood.return_value.choices[0].message.content = "happy"
        api_client.post("/analyze-mood", json={"user_input": "I had a great day!"})

    with patch('app.main.client.chat.completions.create') as mock_suggest:
        mock_suggest.return_value = [] # End stream immediately
        api_client.get("/suggest-activity")
        
        call_args = mock_suggest.call_args.kwargs['messages'][0]['content']
        assert "Role: You are an expert Wellbeing Coach" in call_args
        assert "exactly three personalized 5-minute micro-activities" in call_args

@pytest.mark.unit
def test_suggest_activity_streaming_headers(api_client):
    """Validates that the endpoint returns the correct media type for streaming."""
    _clear_suggest_state(api_client)
    
    # Pre-set mood
    with patch('app.main.client.chat.completions.create') as mock_mood:
        mock_mood.return_value.choices[0].message.content = "calm"
        api_client.post("/analyze-mood", json={"user_input": "I am relaxing."})

    with patch('app.main.client.chat.completions.create') as mock_suggest:
        mock_suggest.return_value = []
        response = api_client.get("/suggest-activity")
        
        assert response.headers["Content-Type"] == "text/event-stream; charset=utf-8"




@pytest.mark.unit
def test_suggest_activity_db_connection_failure(api_client):
    """Tests how the stream handles a database connection crash mid-stream."""
    _clear_suggest_state(api_client)

    with patch('app.main.client.chat.completions.create') as mock_mood:
        mock_mood.return_value.choices[0].message.content = "sad"
        api_client.post("/analyze-mood", json={"user_input": "I feel lonely."})

    with patch('app.main.client.chat.completions.create') as mock_suggest, \
         patch('app.routes.analyze_suggest.get_connection') as mock_db:
        
        # AI returns content, but DB connection fails
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "Listen to music."
        mock_suggest.return_value = [chunk]
        
        mock_db.side_effect = Exception("DB Connection Refused")

        response = api_client.get("/suggest-activity")
        # Since it's a stream, the HTTP status is already 200, 
        # but the error is yielded in the body
        assert "[ERROR: DB Connection Refused]" in response.text

@pytest.mark.unit
def test_suggest_activity_empty_ai_response(api_client):
    """Handles cases where the AI provider returns an empty stream."""
    _clear_suggest_state(api_client)

    # 1. Setup mood
    with patch('app.main.client.chat.completions.create') as mock_mood:
        mock_mood.return_value.choices[0].message.content = "neutral"
        api_client.post("/analyze-mood", json={"user_input": "Just a normal day."})

    # 2. Patch BOTH the AI client and the DB connection
    # Ensure the path matches your import: 'app.routes.analyze_suggest.get_connection'
    with patch('app.main.client.chat.completions.create') as mock_suggest, \
         patch('app.routes.analyze_suggest.get_connection') as mock_db:
        
        # Simulate empty AI stream
        mock_suggest.return_value = iter([])

        # Mock DB cursor
        mock_conn = mock_db.return_value
        mock_cur = mock_conn.cursor.return_value
        mock_cur.fetchone.return_value = ["mock-id-empty"]

        response = api_client.get("/suggest-activity")
        
        assert response.status_code == 200
        assert "Activity ID: mock-id-empty" in response.text
        
        # Verify that the DB was called with an empty string for instructions
        # call_args[0][1] is the tuple of values (%s, %s) -> (mood, instructions)
        db_insert_values = mock_cur.execute.call_args[0][1]
        assert db_insert_values[1] == ""

@pytest.mark.unit
def test_suggest_activity_streaming(api_client):
    _clear_suggest_state(api_client)

    with patch('app.main.client.chat.completions.create') as mock_create:
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello "
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "world!"
        mock_create.return_value = [chunk1, chunk2]

        # Set mood so endpoint will proceed to generate suggestion
        with patch('app.main.client.chat.completions.create') as mock_analyze:
            mock_analyze.return_value.choices[0].message.content = "anxious"
            api_client.post("/analyze-mood", json={"user_input": "I'm feeling overwhelmed with work and family responsibilities."})

        response = api_client.get("/suggest-activity")
        assert response.status_code == 200
        assert "Hello world!" in response.text
