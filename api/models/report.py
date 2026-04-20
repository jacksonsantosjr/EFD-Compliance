# -*- coding: utf-8 -*-
"""
Pydantic models para relatórios e exportação.
"""
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class ExportFormat(str, Enum):
    """Formatos de exportação disponíveis."""
    DOCX = "docx"
    PDF = "pdf"


class ExportRequest(BaseModel):
    """Requisição de exportação de relatório."""
    analysis_id: str
    format: ExportFormat = ExportFormat.DOCX


class ExportResponse(BaseModel):
    """Resposta da exportação."""
    filename: str
    format: str
    file_path: str
    size_bytes: int
