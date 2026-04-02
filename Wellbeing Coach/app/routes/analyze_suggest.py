
"""Routes for mood analysis and activity suggestion endpoints.

This module provides two main endpoints:
- POST /analyze-mood: Analyzes user's emotional state using LLM
- GET /suggest-activity: Generates personalized 5-minute micro-activities

Both endpoints are rate-limited to 2 requests per minute to manage API costs.
"""

from fastapi import APIRouter, Request, HTTPException

from fastapi.responses import StreamingResponse
from openai import OpenAI, RateLimitError
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.analysemodel import UserRequest, AnalyseResponse
from app.db.db_connection import get_connection


# Initialize router with descriptive tags
router = APIRouter(tags=["Emotional Assessment & Activity Generation"])
# Create rate limiter using client IP address as key
limiter = Limiter(key_func=get_remote_address)

def analyse_suggest_router(client: OpenAI, model: str):
    """Factory function to create the analyze-suggest router.
    
    Args:
        client (OpenAI): OpenAI client for LLM API calls
        model (str): Model name to use for completions (e.g., 'gemini-pro')
    
    Returns:
        APIRouter: Configured router with mood analysis and activity suggestion endpoints
    """

    # Shared state: Store the user's analyzed emotion for use in activity suggestion
    capture_user_emotion = {}

    @router.post("/analyze-mood", response_model= AnalyseResponse, summary="Emotional State Assessment")
    @limiter.limit("2/minute")
    def user_emotion(request: Request, input: UserRequest):
        """Analyze user's emotional state and store it for later suggestion generation.
        
        Args:
            request (Request): FastAPI request object
            input (UserRequest): User input containing the text to analyze
        
        Returns:
            AnalyseResponse: Contains the detected emotion
        
        Raises:
            HTTPException: 429 if rate limit exceeded, 500 for other errors
        """
        # Construct LLM prompt for emotion analysis
        userprompt = (f"""
            You are an expert Wellbeing Coach. Analyze the following user input to identify their emotional state.
            User Input: "{input.user_input}"
            Determine the emotion state in one word (e.g., happy, sad, anxious, etc.)  
            """).strip()
        try:
            # Call the LLM API to generate emotion analysis
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": userprompt}],
            )
            llm_response = response.choices[0].message.content
            # Store emotion in shared state for activity suggestion endpoint
            capture_user_emotion["emotion"] = llm_response
            
            # Store mood analysis in database
            conn = get_connection()
            cur = conn.cursor()
            try:
                # Insert user input and detected mood into mood_analysis table
                cur.execute("""
                INSERT INTO mood_analysis (user_input, mood)
                VALUES (%s,%s)
                RETURNING id
                """, (input.user_input, capture_user_emotion["emotion"]))              
            except KeyError as e:
                raise Exception("Missing key:", e)
            except TypeError as e:
                raise Exception("Invalid type:", e)
            
            conn.commit()
            cur.close()
            conn.close()
                
            return AnalyseResponse(emotion=llm_response)
        except RateLimitError as e:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "API rate limit exceeded",
                    "message": "The AI provider's rate limit has been reached. Please wait a moment and try again.",
                    "type": "api_rate_limit_error",
                },
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    @router.get("/suggest-activity", summary="Generate Personalized 5-Minute Booster")
    @limiter.limit("2/minute")
    def suggest_activity(request: Request):
        """Generate personalized 5-minute micro-activities based on analyzed mood.
        
        Returns a server-sent event (SSE) stream of activity suggestions tailored
        to the user's emotional state. Activities are designed to be completed
        in approximately 5 minutes.
        
        Args:
            request (Request): FastAPI request object
        
        Returns:
            StreamingResponse: Server-sent events stream with activity suggestions
        
        Raises:
            HTTPException: 400 if mood not analyzed first, 429 if rate limited, 500 for errors
        """
        try:
            # Ensure mood was analyzed in previous call
            if not capture_user_emotion:
                raise HTTPException(
                status_code=400, 
                detail="I can't suggest the right activity without knowing your current mood. Tell me how you're doing at /analyze-mood first!"
            )

            # Construct LLM prompt for activity suggestions
            activity_prompt = f"""
                Role: You are an expert Wellbeing Coach.
                Task: Based on the user's detected emotion ({capture_user_emotion['emotion']}), 
                suggest exactly three personalized 5-minute micro-activities.
                Constraints:
                    - Keep the tone empathetic yet practical.
                    - Format as a bulleted list.
                    - Total response must be under 5 lines.
                    - Focus on different categories (e.g., Physical Exercise, Mental Exercise, or Sensory Grounding).
                """
    
            def stream_ai_response():
                """Generator function to stream activity suggestions from LLM.
                
                Yields chunks of activity suggestions as they're generated,
                then stores the complete activity in the database.
                """
                try:
                    # Create streaming request to LLM for activity suggestions
                    stream = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": activity_prompt}],
                        stream=True
                    )
                    
                    # Collect chunks and yield them to client as they arrive
                    full_response = ""
                    for chunk in stream:
                        word = chunk.choices[0].delta.content or ""
                        if word:
                            full_response += word
                            yield f"{word}"
                    # Signal end of suggestions
                    yield "\n\n"

                    # Store the complete activity suggestions in database
                    conn = get_connection()
                    cur = conn.cursor()
                    try:
                        cur.execute("""
                        INSERT INTO activities (mood, instructions)
                        VALUES (%s,%s)
                        RETURNING activity_id
                        """, (capture_user_emotion["emotion"], full_response))              
                    except KeyError as e:
                        raise Exception("Missing key:", e)
                    except TypeError as e:
                        raise Exception("Invalid type:", e)
                    # Retrieve the auto-generated activity ID
                    activity_id = cur.fetchone()[0]
                    conn.commit()
                    cur.close()
                    conn.close()
                    # Send activity ID to complete the response
                    yield f"\nActivity ID: {activity_id}\n"
                except Exception as error:
                    yield f"data: [ERROR: {str(error)}]\n\n"
            
            # Create streaming response with server-sent events
            response = StreamingResponse(stream_ai_response(), media_type="text/event-stream") 
            return response
        except RateLimitError as e:
            # Handle OpenAI API rate limiting
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "API rate limit exceeded",
                    "message": "The AI provider's rate limit has been reached. Please wait a moment and try again.",
                    "type": "api_rate_limit_error",
                },
            )
    
    # Return the configured router for inclusion in the FastAPI application
    return router
