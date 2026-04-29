from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import FileResponse

from api.models.report import ExportFormat
from api.config import UPLOADS_DIR
from api.auth import get_current_user, log_audit_event
from database.client import supabase

router = APIRouter()

@router.get("/export/{analysis_id}/{format}")
async def export_report(
    analysis_id: str, 
    format: ExportFormat, 
    current_user = Security(get_current_user)
):
    """
    Exporta o dossiê técnico de uma análise em formato DOCX ou PDF.
    Garante que o usuário só baixe arquivos que ele mesmo processou.
    """
    # 1. Validar propriedade do arquivo no Supabase (Isolamento de Dados)
    try:
        response = supabase.table("sped_analyses") \
            .select("filename, file_hash") \
            .eq("id", analysis_id) \
            .eq("user_id", current_user.id) \
            .single() \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Análise não encontrada ou acesso negado.")
            
        filename = response.data["filename"]
        file_hash = response.data["file_hash"]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao validar propriedade: {e}")
        raise HTTPException(status_code=500, detail="Erro ao validar permissões de acesso.")

    # 2. Localizar arquivo físico
    file_path = UPLOADS_DIR / f"{file_hash}_{filename}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo original não localizado no servidor.")

    try:
        from parser.sped_parser import parse_sped_file
        from validators.base_validator import BaseValidator
        from reports.dossie_generator import DossieGenerator

        parsed = parse_sped_file(file_path)
        validator = BaseValidator(parsed)
        # O validate agora é assíncrono em algumas partes do sistema, mas aqui usamos o síncrono do BaseValidator
        result = await validator.validate() if hasattr(validator.validate, "__await__") else validator.validate()

        generator = DossieGenerator(result)

        if format == ExportFormat.DOCX:
            output_path = generator.generate_docx()
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            output_path = generator.generate_pdf()
            media_type = "application/pdf"

        # 3. Registrar Log de Auditoria
        await log_audit_event(
            user_id=current_user.id,
            action="export_report",
            target_id=analysis_id,
            details={"format": format, "filename": filename}
        )

        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type=media_type,
        )

    except Exception as e:
        print(f"Erro na geração do relatório: {e}")
        msg = "Ocorreu um erro interno ao gerar o relatório solicitado."
        
        # Manter aviso específico para desenvolvedor sobre bibliotecas PDF no Windows
        if any(lib in str(e).lower() for lib in ["weasyprint", "cairo", "pango"]):
            msg = "ATENÇÃO: O servidor de desenvolvimento carece das bibliotecas nativas para exportação de PDF. Por favor, utilize o formato DOCX."
        
        raise HTTPException(status_code=500, detail=msg)
