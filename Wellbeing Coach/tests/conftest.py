"""Pytest Configuration and Shared Fixtures"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path so we can import 'app' module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.routes import analyze_suggest
from app.routes import feedback_history
from app.db.db_connection import get_connection

@pytest.fixture
def api_client(request):
    """Test client fixture with configurable rate limiting.
    
    Disables rate limiting for unit tests (marked with @pytest.mark.unit)
    to allow rapid testing without hitting rate limits. Keeps rate limiting
    enabled for integration tests to validate real API behavior.
    
    Args:
        request: pytest request object containing test markers
    
    Yields:
        TestClient: FastAPI test client with appropriate rate limiting configuration
    """
    # Check if test is marked as 'unit'
    is_unit_test = any(mark.name == 'unit' for mark in request.node.iter_markers())

    # Store original limiter states for restoration after test
    original_app_enabled = app.state.limiter.enabled
    original_analyze_enabled = analyze_suggest.limiter.enabled
    original_feedback_enabled = feedback_history.limiter.enabled

    if is_unit_test:
        # Disable rate limiting for fast unit test execution
        app.state.limiter.enabled = False
        analyze_suggest.limiter.enabled = False
        feedback_history.limiter.enabled = False
        
    else:
        # Ensure rate limiting is enabled for integration tests
        app.state.limiter.enabled = True
        analyze_suggest.limiter.enabled = True
        feedback_history.limiter.enabled = True

    # Yield test client to test function
    yield TestClient(app, raise_server_exceptions=False)

    # Restore original limiter states after test completes
    app.state.limiter.enabled = original_app_enabled
    analyze_suggest.limiter.enabled = original_analyze_enabled
    feedback_history.limiter.enabled = original_feedback_enabled


@pytest.fixture
def db_connection():
    """Database connection fixture for tests requiring direct DB access.
    
    Provides a database connection that rolls back changes after the test
    to maintain test isolation and prevent side effects.
    
    Yields:
        Connection: Database connection object
    """
    conn = get_connection()
    yield conn
    # Rollback any changes to prevent affecting other tests
    conn.rollback()
    conn.close()

# API rate limiting configuration
RATE_LIMIT_PER_MINUTE = 2

