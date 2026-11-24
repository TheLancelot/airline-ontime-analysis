from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.dashboard import router as dashboard_router
from app.config import BASE_DIR

app = FastAPI(title="Airline DBMS Project")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(dashboard_router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
    return response


@app.get("/")
async def landing_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {})


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@app.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {})


@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {})


@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html", {})


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "airline-security-demo"}
