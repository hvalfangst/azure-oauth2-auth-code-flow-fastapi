# server/main.py

from fastapi import FastAPI

from server.routers import heroes

app = FastAPI(
    title="Hero API",
    description="An API to manage heroes secure by OAuth 2.0 auth code flow",
    version="1.0.0"
)

app.include_router(heroes.router, prefix="/api", tags=["Heroes"])