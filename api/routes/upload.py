# -*- coding: utf-8 -*-
"""
Rotas de upload e processamento de arquivos SPED.
"""
import hashlib
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from api.config import UPLOADS_DIR, MAX_FILE_SIZE_BYTES
from api.models.sped_file import AnalysisResult

router = APIRouter()


@router.post("/upload", response_model=AnalysisResult)
async def upload_sped_file(
    files: List[UploadFile] = File(...),
    obrigacao: str = Query("efd", description="Tipo de obrigação acessória (efd, ecd, ecf)")
):
    """
    Upload e análise de arquivos SPED (EFD, ECD, ECF) e/ou XMLs de NF-e.
    Obrigatório: 1 arquivo .txt (SPED).
    Opcional: Múltiplos arquivos .xml (NF-es) para cruzamento (Fase 2 da EFD).
    """
    sped_file = None
    xml_data_list = []
    
    # Separar arquivos por tipo
    for file in files:
        if file.filename.endswith(".txt"):
            sped_file = file
        elif file.filename.endswith(".xml"):
            xml_content = await file.read()
            from parser.xml_parser import parse_nfe_xml
            nfe_data = parse_nfe_xml(xml_content)
            if nfe_data:
                xml_data_list.append(nfe_data)
        
    if not sped_file:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo SPED (.txt) encontrado no upload."
        )

    # Ler conteúdo do SPED
    content = await sped_file.read()

    # Validar tamanho
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
        )

    # Calcular hash do arquivo
    file_hash = hashlib.sha256(content).hexdigest()

    # Salvar arquivo SPED
    file_path = UPLOADS_DIR / f"{file_hash}_{sped_file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # ROTEAMENTO DE OBRIGAÇÃO ACESSÓRIA
        obrigacao = obrigacao.lower()
        
        if obrigacao == "efd":
            from parser.sped_parser import parse_sped_file
            parsed = parse_sped_file(file_path)

            if not parsed.get_registro_unico("0000"):
                raise HTTPException(status_code=400, detail="Arquivo não reconhecido como SPED EFD ICMS/IPI. Registro 0000 ausente.")

            from validators.base_validator import BaseValidator
            validator = BaseValidator(parsed, xml_data=xml_data_list)
            result = await validator.validate()

        elif obrigacao == "ecd":
            from parser.ecd_parser import parse_ecd_file
            from validators.ecd.base_validator_ecd import ECDValidator
            
            parsed = parse_ecd_file(file_path)
            
            # Validação rápida de Cabeçalho (Bloco 0) para ECD
            if not parsed.get_registro_unico("0000"):
                raise HTTPException(status_code=400, detail="Arquivo não reconhecido como ECD. Registro 0000 ausente.")
                
            validator = ECDValidator(parsed)
            result = await validator.validate()

        elif obrigacao == "ecf":
            from parser.ecf_parser import parse_ecf_file
            from validators.ecf.base_validator_ecf import ECFValidator
            
            parsed = parse_ecf_file(file_path)
            
            if not parsed.get_registro_unico("0000"):
                raise HTTPException(status_code=400, detail="Arquivo não reconhecido como ECF. Registro 0000 ausente.")
                
            validator = ECFValidator(parsed)
            result = await validator.validate()
        
        else:
            raise HTTPException(status_code=400, detail=f"Obrigação desconhecida: {obrigacao}")

        # Atualizar com nome original do arquivo
        result.filename = sped_file.filename
        result.file_hash = file_hash

        # Salvar no Supabase (se configurado)
        from database.client import supabase
        if supabase:
            try:
                dt_ini = result.file_info.periodo_ini.isoformat() if result.file_info.periodo_ini else None
                dt_fin = result.file_info.periodo_fin.isoformat() if result.file_info.periodo_fin else None
                
                payload = {
                    "id": result.id,
                    "filename": result.filename,
                    "file_hash": result.file_hash,
                    "cnpj": result.file_info.cnpj,
                    "razao_social": result.file_info.razao_social,
                    "uf": result.file_info.uf,
                    "periodo_ini": dt_ini,
                    "periodo_fin": dt_fin,
                    "score": result.score,
                    "total_registros": result.total_registros,
                    "result_json": result.model_dump(mode="json")
                }
                supabase.table("sped_analyses").insert(payload).execute()
                print(f"Análise salva no Supabase (ID: {result.id})")
            except Exception as db_err:
                print(f"Erro ao salvar no Supabase: {db_err}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


@router.post("/upload/compare")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Upload de múltiplos arquivos SPED para comparação entre períodos.
    """
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="Envie ao menos 2 arquivos para comparação entre períodos."
        )

    if len(files) > 12:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 12 arquivos por comparação (1 ano)."
        )

    results = []
    for file in files:
        if not file.filename.endswith(".txt"):
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo '{file.filename}' não é .txt."
            )

        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        file_path = UPLOADS_DIR / f"{file_hash}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)

        try:
            from parser.sped_parser import parse_sped_file
            from validators.base_validator import BaseValidator

            parsed = parse_sped_file(file_path)
            validator = BaseValidator(parsed)
            result = await validator.validate()
            result.filename = file.filename
            result.file_hash = file_hash
            results.append(result)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar '{file.filename}': {str(e)}"
            )

    # Ordenar por período
    results.sort(key=lambda r: r.file_info.periodo_ini or "")

    return {
        "message": f"{len(results)} arquivos processados.",
        "analyses": [r.model_dump() for r in results],
        "total_files": len(results),
    }
