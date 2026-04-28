# -*- coding: utf-8 -*-
"""
Rotas de upload e processamento de arquivos SPED.
"""
import hashlib
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Security

from api.config import UPLOADS_DIR, MAX_FILE_SIZE_BYTES
from api.models.sped_file import AnalysisResult
from api.auth import get_current_user

router = APIRouter()


@router.post("/upload", response_model=AnalysisResult)
async def upload_sped_file(
    files: List[UploadFile] = File(...),
    obrigacao: str = Query("efd", description="Tipo de obrigação acessória (efd, ecd, ecf)"),
    current_user = Security(get_current_user)
):
    """
    Upload e análise de arquivos SPED (EFD, ECD, ECF) e/ou XMLs de NF-e.
    Obrigatório: 1 arquivo .txt (SPED).
    Opcional: Múltiplos arquivos .xml (NF-es) para cruzamento (Fase 2 da EFD).
    """
    sped_files = []
    xml_data_list = []
    
    # Separar arquivos por tipo
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
            status_code=400,
            detail="Nenhum arquivo SPED (.txt) encontrado no upload."
        )

    # Processar e salvar os arquivos TXT
    saved_files = []
    for s_file in sped_files:
        content = await s_file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail=f"Arquivo excede o limite de {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.")
        f_hash = hashlib.sha256(content).hexdigest()
        f_path = UPLOADS_DIR / f"{f_hash}_{Path(s_file.filename).name}"
        with open(f_path, "wb") as f:
            f.write(content)
        saved_files.append({"path": f_path, "hash": f_hash, "filename": s_file.filename})

    try:
        obrigacao = obrigacao.lower()
        
        # CASO 1: Upload de 1 único arquivo (Fluxo Padrão EFD/ECD/ECF)
        if len(saved_files) == 1:
            f_info = saved_files[0]
            file_path = f_info["path"]
            file_hash = f_info["hash"]
            filename = f_info["filename"]
            
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

            result.filename = filename
            result.file_hash = file_hash

        # CASO 2: Upload de 2 arquivos para Cruzamento (Fase 6)
        elif len(saved_files) == 2 and obrigacao in ["ecd", "ecf"]:
            from parser.ecd_parser import parse_ecd_file
            from parser.ecf_parser import parse_ecf_file
            from validators.ecf.cross_ecd_ecf_validator import CrossEcdEcfValidator
            
            parsed_ecd = None
            parsed_ecf = None
            
            # Identificação dinâmica por leitura da primeira linha
            for f_info in saved_files:
                try:
                    with open(f_info["path"], "r", encoding="latin1") as f:
                        first_line = f.readline()
                        if "LECD" in first_line:
                            parsed_ecd = parse_ecd_file(f_info["path"])
                        elif "LECF" in first_line:
                            parsed_ecf = parse_ecf_file(f_info["path"])
                        else:
                            # Fallback rudimentar pelo nome do arquivo
                            if "ecd" in f_info["filename"].lower():
                                parsed_ecd = parse_ecd_file(f_info["path"])
                            else:
                                parsed_ecf = parse_ecf_file(f_info["path"])
                except Exception:
                    pass
                    
            if not parsed_ecd or not parsed_ecf:
                raise HTTPException(status_code=400, detail="Para o cruzamento, envie 1 arquivo contendo a ECD e 1 contendo a ECF válidos.")
                
            validator = CrossEcdEcfValidator(parsed_ecd, parsed_ecf)
            result = await validator.validate()
            
            result.filename = "Cruzamento ECD x ECF"
            result.file_hash = saved_files[0]["hash"][:16] + saved_files[1]["hash"][:16]

        else:
            raise HTTPException(status_code=400, detail="Quantidade de arquivos TXT incompatível com a obrigação selecionada.")


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
                    "result_json": result.model_dump(mode="json"),
                    "user_id": current_user.id
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
        file_path = UPLOADS_DIR / f"{file_hash}_{Path(file.filename).name}"
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
