# -*- coding: utf-8 -*-
"""
Rotas de upload e processamento de arquivos SPED.
"""
import hashlib
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from api.config import UPLOADS_DIR, MAX_FILE_SIZE_BYTES
from api.models.sped_file import AnalysisResult, SpedFileInfo

router = APIRouter()


@router.post("/upload", response_model=AnalysisResult)
async def upload_sped_file(file: UploadFile = File(...)):
    """
    Upload e análise de um arquivo SPED EFD ICMS/IPI.
    Recebe o arquivo .txt validado pelo PVA, processa e retorna o resultado.
    """
    # Validar tipo de arquivo
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Envie um arquivo .txt do SPED EFD."
        )

    # Ler conteúdo
    content = await file.read()

    # Validar tamanho
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
        )

    # Calcular hash do arquivo
    file_hash = hashlib.sha256(content).hexdigest()

    # Salvar arquivo temporariamente
    file_path = UPLOADS_DIR / f"{file_hash}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    # TODO: Integrar com parser e validadores (Tasks 1.2, 1.3, 2.x)
    # Por enquanto, retorna resultado stub
    result = AnalysisResult(
        filename=file.filename,
        file_hash=file_hash,
        file_info=SpedFileInfo(total_linhas=content.count(b"\n")),
        total_registros=content.count(b"\n"),
        score=0.0,
    )

    return result


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

    # TODO: Processar cada arquivo e executar comparação (Tasks 4.2, 6.6)
    return {
        "message": f"{len(files)} arquivos recebidos para comparação.",
        "status": "processing"
    }
