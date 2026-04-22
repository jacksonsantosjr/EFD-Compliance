# -*- coding: utf-8 -*-
"""
Rotas de exportação de relatórios (DOCX / PDF).
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models.report import ExportFormat
from api.config import UPLOADS_DIR

router = APIRouter()


@router.get("/export/{analysis_id}/{format}")
async def export_report(analysis_id: str, format: ExportFormat):
    """
    Exporta o dossiê técnico de uma análise em formato DOCX ou PDF.
    Reprocessa o arquivo para gerar o relatório sob demanda.
    """
    # Procurar arquivo pelo ID no diretório de uploads
    upload_files = list(UPLOADS_DIR.glob(f"*"))
    if not upload_files:
        raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado.")

    # Para v1, usar o último arquivo processado
    # TODO: Implementar lookup por analysis_id via banco de dados
    latest_file = max(upload_files, key=lambda f: f.stat().st_mtime)

    try:
        from parser.sped_parser import parse_sped_file
        from validators.base_validator import BaseValidator
        from reports.dossie_generator import DossieGenerator

        parsed = parse_sped_file(latest_file)
        validator = BaseValidator(parsed)
        result = validator.validate()

        generator = DossieGenerator(result)

        if format == ExportFormat.DOCX:
            output_path = generator.generate_docx()
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            output_path = generator.generate_pdf()
            media_type = "application/pdf"

        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type=media_type,
        )

    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Dependência não instalada: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar relatório: {str(e)}"
        )
