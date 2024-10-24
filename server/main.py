# server/main.py

import uvicorn
from fastapi import FastAPI

from server.routers import heroes

app = FastAPI(
    title="Hero API",
    description="An API to manage heroes secure by OAuth 2.0 auth code flow",
    version="1.0.0"
)

app.include_router(heroes.router, prefix="/api", tags=["Heroes"])

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)
