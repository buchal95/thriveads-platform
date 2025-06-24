"""
Minimal debug version for Railway deployment
"""

from fastapi import FastAPI
import os
import uvicorn

# Create minimal FastAPI app
app = FastAPI(title="ThriveAds Debug API")

@app.get("/")
async def root():
    return {"message": "ThriveAds Debug API is running!"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "meta_token_set": bool(os.getenv("META_ACCESS_TOKEN"))
    }

@app.get("/env")
async def check_env():
    """Check environment variables (for debugging)"""
    return {
        "PORT": os.getenv("PORT"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else None,
        "META_ACCESS_TOKEN": "***" if os.getenv("META_ACCESS_TOKEN") else None,
        "SECRET_KEY": "***" if os.getenv("SECRET_KEY") else None,
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting debug server on port {port}")
    uvicorn.run(
        "debug_main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
