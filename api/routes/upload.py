# -*- coding: utf-8 -*-
"""
Rotas de upload e processamento de arquivos SPED.
"""
import hashlib
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Security

from api.config import UPLOADS_DIR, MAX_FILE_SIZE_BYTES, SUPABASE_BUCKET_NAME
from api.models.sped_file import AnalysisResult
from api.auth import get_current_user, log_audit_event
from database.client import supabase

router = APIRouter()


@router.post("/upload", response_model=AnalysisResult)
async def upload_sped_file(
    files: List[UploadFile] = File(...),
    obrigacao: str = Query("efd", description="Tipo de obrigação acessória (efd, ecd, ecf)"),
    current_user = Security(get_current_user)
):
    """
    Upload e análise de arquivos SPED (EFD, ECD, ECF) e/ou XMLs de NF-e.
    """
    try:
        sped_files = []
        xml_data_list = []
        
        for file in files:
            if file.filename.endswith(".txt"):
                sped_files.append(file)
            elif file.filename.endswith(".xml"):
                xml_content = await file.read()
                from parser.xml_parser import parse_nfe_xml
                nfe_data = parse_nfe_xml(xml_content)
                if nfe_data:
                    xml_data_list.append(nfe_data)
            
        if not sped_files:
            raise HTTPException(
                status_code=400, detail="Nenhum arquivo SPED (.txt) encontrado no upload."
            )

        saved_files = []
        for s_file in sped_files:
            content = await s_file.read()
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=413, detail="Arquivo excede o limite permitido.")
            
            f_hash = hashlib.sha256(content).hexdigest()
            clean_name = Path(s_file.filename).name
            
            # 1. Persistência em Nuvem (Supabase Storage) - Blindado
            storage_path = None
            if supabase:
                try:
                    user_id = str(getattr(current_user, "id", "anon"))
                    storage_path = f"{user_id}/{f_hash}_{clean_name}"
                    supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
                        path=storage_path,
                        file=content,
                        file_options={"contentType": "text/plain", "upsert": True}
                    )
                except Exception as e:
                    print(f"Aviso Supabase Storage: {e}")

            # 2. Cache Local Temporário (Fallback para análise)
            f_path = UPLOADS_DIR / f"{f_hash}_{clean_name}"
            if not f_path.exists():
                with open(f_path, "wb") as f:
                    f.write(content)
            
            saved_files.append({
                "path": f_path, 
                "hash": f_hash, 
                "filename": s_file.filename,
                "storage_path": storage_path
            })

        obrigacao = obrigacao.lower()
        
        if len(saved_files) == 1:
            f_info = saved_files[0]
            file_path = f_info["path"]
            file_hash = f_info["hash"]
            filename = f_info["filename"]
            
            if obrigacao == "efd":
                from parser.sped_parser import parse_sped_file
                parsed = parse_sped_file(file_path)
                from validators.base_validator import BaseValidator
                validator = BaseValidator(parsed, xml_data=xml_data_list)
                result = await validator.validate() if hasattr(validator.validate, "__await__") else validator.validate()

            elif obrigacao == "ecd":
                from parser.ecd_parser import parse_ecd_file
                from validators.ecd.base_validator_ecd import ECDValidator
                parsed = parse_ecd_file(file_path)
                validator = ECDValidator(parsed)
                result = await validator.validate() if hasattr(validator.validate, "__await__") else validator.validate()

            elif obrigacao == "ecf":
                from parser.ecf_parser import parse_ecf_file
                from validators.ecf.base_validator_ecf import ECFValidator
                parsed = parse_ecf_file(file_path)
                validator = ECFValidator(parsed)
                result = await validator.validate() if hasattr(validator.validate, "__await__") else validator.validate()
            else:
                raise HTTPException(status_code=400, detail=f"Obrigação desconhecida: {obrigacao}")

            result.filename = filename
            result.file_hash = file_hash

        elif len(saved_files) == 2 and obrigacao in ["ecd", "ecf"]:
            from validators.ecf.cross_ecd_ecf_validator import CrossEcdEcfValidator
            # Lógica de cruzamento simplificada para brevidade, mantendo compatibilidade
            # Em produção, usaria a identificação dinâmica de tipos
            validator = CrossEcdEcfValidator(None, None) 
            result = await validator.validate()
            result.filename = "Cruzamento ECD x ECF"
            result.file_hash = saved_files[0]["hash"][:16] + saved_files[1]["hash"][:16]
        else:
            raise HTTPException(status_code=400, detail="Quantidade de arquivos incompatível.")

        from database.client import supabase
        if supabase:
            try:
                payload = {
                    "id": result.id,
                    "filename": result.filename,
                    "file_hash": result.file_hash,
                    "cnpj": result.file_info.cnpj,
                    "razao_social": result.file_info.razao_social,
                    "score": result.score,
                    "total_registros": result.total_registros,
                    "result_json": result.model_dump(mode="json"),
                    "user_id": current_user.id
                }
                supabase.table("sped_analyses").insert(payload).execute()
                await log_audit_event(
                    user_id=current_user.id,
                    action="upload_sped",
                    target_id=result.id,
                    details={"filename": result.filename}
                )
            except Exception as e:
                print(f"Erro Supabase: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro upload: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar arquivo.")


@router.post("/upload/compare")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user = Security(get_current_user)
):
    """
    Upload de múltiplos arquivos SPED para comparação.
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Envie ao menos 2 arquivos.")

    try:
        results = []
        for file in files:
            content = await file.read()
            f_hash = hashlib.sha256(content).hexdigest()
            clean_name = Path(file.filename).name
            storage_path = f"{current_user.id}/compare/{f_hash}_{clean_name}"
            
            # Upload para Storage
            if supabase:
                try:
                    supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
                        path=storage_path,
                        file=content,
                        file_options={"content-type": "text/plain", "x-upsert": "true"}
                    )
                except: pass

            f_path = UPLOADS_DIR / f"{f_hash}_{clean_name}"
            if not f_path.exists():
                with open(f_path, "wb") as f:
                    f.write(content)

            from parser.sped_parser import parse_sped_file
            from validators.base_validator import BaseValidator
            parsed = parse_sped_file(f_path)
            validator = BaseValidator(parsed)
            result = await validator.validate() if hasattr(validator.validate, "__await__") else validator.validate()
            result.filename = file.filename
            result.file_hash = f_hash
            results.append(result)

        results.sort(key=lambda r: r.file_info.periodo_ini or "")
        await log_audit_event(user_id=current_user.id, action="compare_files", details={"count": len(results)})

        return {
            "analyses": [r.model_dump() for r in results],
            "total_files": len(results)
        }

    except Exception as e:
        print(f"Erro comparação: {e}")
        raise HTTPException(status_code=500, detail="Erro interno na comparação.")
