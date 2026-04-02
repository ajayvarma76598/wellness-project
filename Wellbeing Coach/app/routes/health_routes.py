"""
Health Check Routes

This module contains health check endpoints for system monitoring.
"""

from fastapi import APIRouter

# Create router for health check endpoints
router = APIRouter(tags=["System"])


@router.get("/health")
def health_check():
    """
    Check API health status.
    
    This endpoint is used by monitoring tools and load balancers
    to verify that the API service is running and responsive.
    
    Returns:
        dict: Health status information including service status
    """
    return {
        "status": "healthy",
        "service": "llm-query-api",
        "version": "1.0.0"
    }
