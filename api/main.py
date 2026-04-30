# -*- coding: utf-8 -*-
"""
EFD Compliance — FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, API_CORS_ORIGINS
from api.routes import upload, analysis, export


def create_app() -> FastAPI:
    """Cria e configura a instância FastAPI."""
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=API_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Rotas
    app.include_router(upload.router, prefix="/api", tags=["Upload"])
    app.include_router(analysis.router, prefix="/api", tags=["Análise"])
    app.include_router(export.router, prefix="/api", tags=["Exportação"])

    @app.get("/health", tags=["Sistema"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": APP_NAME,
            "version": APP_VERSION
        }

    @app.get("/", tags=["Sistema"])
    async def root():
        """Root endpoint — informações da API."""
        return {
            "app": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "docs": "/docs"
        }

    return app


app = create_app()
