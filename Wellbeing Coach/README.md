# Wellbeing Coach: Personalized Mental Booster API

A Python-based AI coach that analyzes emotional cues and suggests personalized 5-minute micro-activities to reduce stress and burnout.

## Description

This FastAPI application serves as a wellbeing coach API that uses AI to analyze user emotions from text input and provides tailored micro-activities to improve mental health. It integrates with OpenAI's API (configured for Gemini) and stores data in a PostgreSQL database.

## Features

- **Emotional Analysis**: Analyze user input to detect emotional states
- **Personalized Suggestions**: Generate 5-minute micro-activities based on detected emotions
- **Feedback System**: Allow users to rate and comment on suggested activities
- **History Tracking**: View past mood analyses and activity suggestions
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **CORS Support**: Cross-origin resource sharing enabled
- **Health Checks**: System monitoring endpoints

## Installation

### Prerequisites

- Python 3.12 or higher
- PostgreSQL database
- OpenAI API key (configured for Gemini)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd wellbeing-coach
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_openai_api_key_here
   GEMINI_BASE_URL=https://api.openai.com/v1  # or your custom base URL
   GEMINI_MODEL_NAME=gpt-3.5-turbo  # or your preferred model

   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=wellbeing_coach
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   ```

4. Ensure PostgreSQL is running and the database exists.

5. Run the application:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Health Check
- **GET /health**
  - Description: Check API health status
  - Response: JSON with status, service name, and version

### Emotional Assessment & Activity Generation
- **POST /analyze-mood**
  - Description: Analyze user input to identify emotional state
  - Rate Limit: 2 requests per minute
  - Request Body:
    ```json
    {
      "user_input": "I'm feeling overwhelmed with work today."
    }
    ```
  - Response:
    ```json
    {
      "emotion": "anxious"
    }
    ```
  - Stores mood analysis in database

- **GET /suggest-activity**
  - Description: Generate personalized 5-minute micro-activities based on analyzed emotion
  - Rate Limit: 2 requests per minute
  - Response: Streaming text with activity suggestions and activity ID
  - Requires prior mood analysis
  - Stores activity in database

### Feedback and History
- **POST /feedback**
  - Description: Submit feedback for a suggested activity
  - Request Body:
    ```json
    {
      "activity_id": "uuid-here",
      "rating": 4,
      "effective": true,
      "comment": "This helped me relax."
    }
    ```
  - Response: Confirmation message

- **GET /history**
  - Description: Retrieve history of mood analyses and activity suggestions
  - Response:
    ```json
    {
      "history": [
        {
          "user_input": "I'm overwhelmed",
          "mood": "anxious",
          "suggestions": "1. Deep breathing exercise..."
        }
      ]
    }
    ```

## Database Schema

The application uses PostgreSQL with the following tables:

### mood_analysis
- `id` (UUID, Primary Key)
- `user_input` (TEXT, NOT NULL)
- `mood` (VARCHAR(50))
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### activities
- `activity_id` (UUID, Primary Key)
- `mood` (VARCHAR(50))
- `instructions` (TEXT)
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### feedback
- `id` (UUID, Primary Key)
- `activity_id` (UUID, Foreign Key to activities.activity_id)
- `rating` (INT)
- `effective` (BOOLEAN)
- `comment` (TEXT)
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

Tables are automatically created on application startup via `create_tables()` function in `db_connection.py`.

## Database Connection

Database connection is handled in `app/db/db_connection.py`:

- Uses `psycopg2` for PostgreSQL connectivity
- Environment variables for connection parameters
- Automatic table creation on startup
- Connection pooling not implemented (uses direct connections)

## Testing

Run tests using pytest:

```bash
uv run pytest
```

Tests are located in the `tests/` directory:
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`

Coverage reports are generated in `htmlcov/` directory.

## Dependencies

Key dependencies from `pyproject.toml`:
- `fastapi`: Web framework
- `openai`: AI API client
- `psycopg2`: PostgreSQL driver
- `pytest`: Testing framework
- `slowapi`: Rate limiting
- `uvicorn`: ASGI server
- `python-dotenv`: Environment variable management

## Development

- Code is organized in `app/` directory
- Models in `app/models/`
- Routes in `app/routes/`
- Database utilities in `app/db/`
- Main application in `app/main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests
5. Submit a pull request

