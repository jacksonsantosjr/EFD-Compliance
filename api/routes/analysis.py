# -*- coding: utf-8 -*-
"""
Rotas de consulta de resultados de análise.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Retorna o resultado completo de uma análise pelo ID.
    """
    # TODO: Buscar do banco de dados (Task 4.3)
    raise HTTPException(
        status_code=404,
        detail=f"Análise {analysis_id} não encontrada."
    )


@router.get("/analyses")
async def list_analyses(limit: int = 20, offset: int = 0):
    """
    Lista o histórico das últimas análises realizadas.
    """
    # TODO: Buscar do Supabase/SQLite (Task 4.6)
    return {
        "analyses": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/comparison/{comparison_id}")
async def get_comparison(comparison_id: str):
    """
    Retorna o resultado de uma comparação entre períodos.
    """
    # TODO: Buscar do banco de dados (Task 4.4)
    raise HTTPException(
        status_code=404,
        detail=f"Comparação {comparison_id} não encontrada."
    )
