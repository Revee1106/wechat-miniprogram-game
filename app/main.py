from fastapi import FastAPI

from app.admin.api import router as admin_router
from app.admin.auth import install_admin_auth
from app.admin.static import create_admin_frontend_router
from app.api.router import api_router


app = FastAPI(title="Wendao Core Loop API")
install_admin_auth(app)
app.include_router(api_router)
app.include_router(admin_router)
app.include_router(create_admin_frontend_router())
