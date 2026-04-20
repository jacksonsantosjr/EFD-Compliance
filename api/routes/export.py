# -*- coding: utf-8 -*-
"""
Rotas de exportação de relatórios (DOCX / PDF).
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models.report import ExportFormat

router = APIRouter()


@router.get("/export/{analysis_id}/{format}")
async def export_report(analysis_id: str, format: ExportFormat):
    """
    Exporta o dossiê técnico de uma análise em formato DOCX ou PDF.
    """
    # TODO: Gerar relatório e retornar arquivo (Tasks 3.1, 3.2, 4.5)
    raise HTTPException(
        status_code=501,
        detail=f"Exportação em {format.value} ainda não implementada."
    )
