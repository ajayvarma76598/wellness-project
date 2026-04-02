"""Routes for user feedback and history retrieval endpoints.

This module provides endpoints for:
- POST /feedback: Submit feedback on activity effectiveness
- GET /history: Retrieve user's mood analysis and activity history

Both endpoints are rate-limited to manage database load.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from app.db.db_connection import get_connection
from app.models.analysemodel import FeedbackRequest
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter using client IP address
limiter = Limiter(key_func=get_remote_address)
# Initialize router with descriptive tags for API documentation
router = APIRouter(tags=["feedback and history generation"])

@router.post("/feedback")
@limiter.limit("2/minute")
def post_feedback(request: Request, data: FeedbackRequest):
    """Submit user feedback on an activity's effectiveness.
    
    Validates that the activity ID exists before storing feedback in the database.
    Allows users to rate activities and provide comments on their effectiveness.
    
    Args:
        request (Request): FastAPI request object
        data (FeedbackRequest): Feedback data including activity_id, rating, and comment
    
    Returns:
        dict: Confirmation message that feedback was saved
    
    Raises:
        HTTPException: 404 if activity not found, 422 for validation errors, 
                      429 if rate limited, 500 for internal errors
    """
    try:
        # Get database connection
        conn = get_connection()
        cur = conn.cursor()
        
        # Verify activity exists before accepting feedback
        cur.execute(
            "SELECT activity_id FROM activities WHERE activity_id=%s",
            (str(data.activity_id),)
        )
        activity = cur.fetchone()

        # Raise error if activity not found
        if not activity:
            raise HTTPException(status_code=404, detail="Activity ID does not exist")
        
        # Insert feedback record into database
        cur.execute("""
        INSERT INTO feedback (activity_id, rating, effective, comment)
        VALUES (%s,%s,%s,%s)                
        """,(str(data.activity_id), data.rating, data.effective, data.comment))
    except HTTPException as e:
        raise e
    except RequestValidationError:
        raise HTTPException(status_code=422, detail="Request data validation error")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()
    
    return {"message": "Feedback saved"}

@router.get("/history")
@limiter.limit("2/minute")
def get_history(request: Request):
    """Retrieve user's complete mood analysis and activity suggestion history.
    
    Fetches all past mood analyses and their associated suggested activities,
    allowing users to review their emotional journey and activity recommendations.
    
    Args:
        request (Request): FastAPI request object
    
    Returns:
        dict: Dictionary containing a list of history entries with user_input, mood, and suggestions
    
    Raises:
        HTTPException: 404 if no history found, 429 if rate limited, 500 for internal errors
    """
    try:
        # Get database connection
        conn = get_connection()
        cur = conn.cursor()
        
        # Query mood analysis and related activity suggestions
        cur.execute("""
            SELECT m.user_input, m.mood, a.instructions
            FROM mood_analysis m
            JOIN activities a
            ON m.mood = a.mood
            """)

        results = cur.fetchall()
        # Raise error if no history exists
        if not results:
            raise HTTPException(status_code=404, detail="No history found")
        
        # Format results into response structure
        response = {"history": []}
        for result in results:
            response["history"].append({
                "user_input": result[0],
                "mood": result[1],
                "suggestions": result[2]
            })
    except HTTPException as e:
        raise e
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()
    return response