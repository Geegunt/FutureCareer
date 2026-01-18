from fastapi import FastAPI
from app.routes import api
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        dict: Service status.
    """
    return {"status": "ok", "service": "ml"}
