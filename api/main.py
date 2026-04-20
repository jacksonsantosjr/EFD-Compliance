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
