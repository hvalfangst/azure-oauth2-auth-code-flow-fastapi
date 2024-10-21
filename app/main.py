# app/main.py

from fastapi import FastAPI

from app.routers import auth, heroes

app = FastAPI(
    title="Hero API",
    description="An API to manage heroes secure by OAuth 2.0 auth code flow",
    version="1.0.0"
)

# Register the oauth and heroes router
app.include_router(auth.router, prefix="/auth", tags=["OAuth2 Back-channel"])
app.include_router(heroes.router, prefix="/api", tags=["Heroes"])
