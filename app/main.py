# app/main.py

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi  # ✅ Import this for custom OpenAPI

from app.routers import auth_routes, oauth_routes, users, payments, plans, classes, chats
from app.database import engine, Base
from app.config import SECRET_KEY

app = FastAPI(
    title="Gameapp",
    openapi_tags=[
        {"name": "Authentication", "description": "Auth related endpoints"},
        {"name": "OAuth Login", "description": "OAuth login endpoints"},
        {"name": "User", "description": "User profile and management"},
        {"name": "Payment", "description": "Subscription and payments"},
    ],
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# OAuth2 scheme for Swagger UI Authorization button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ✅ Fixed custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="Your Gameapp API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# ✅ Assign the custom OpenAPI generator
app.openapi = custom_openapi

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://93dddca0bf3f.ngrok-free.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://gameplan-demo.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

# Include API routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(oauth_routes.router, prefix="/api/oauth", tags=["OAuth Login"])
app.include_router(users.router, prefix="/api/user", tags=["User"])
app.include_router(payments.router, prefix="/api/payment", tags=["Payment"])
app.include_router(plans.router, prefix="/api/plans", tags=["Plans"])
app.include_router(classes.router, prefix="/api/classes", tags=["Classes"])
app.include_router(chats.router, prefix="/api/chats", tags=["Chats"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Gameapp API"}
