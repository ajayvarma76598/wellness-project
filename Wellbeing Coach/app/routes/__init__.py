from app.routes.health_routes import router as health_router
from app.routes.analyze_suggest import router as analyse_router
from app.routes.feedback_history import router as feedback_history_router
__all__ = ["health_router", "analyse_router", "feedback_history_router"]
