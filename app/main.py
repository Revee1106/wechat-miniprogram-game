from fastapi import FastAPI

from app.api.router import api_router


app = FastAPI(title="Wendao Core Loop API")
app.include_router(api_router)
