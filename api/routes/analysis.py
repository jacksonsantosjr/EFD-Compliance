from fastapi import APIRouter, HTTPException, Security
from api.auth import get_current_user
from database.client import supabase

router = APIRouter()

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, current_user = Security(get_current_user)):
    """
    Retorna o resultado completo de uma análise pelo ID (apenas se pertencer ao usuário).
    """
    try:
        # O RLS do banco cuidará para que o usuário só veja o que é dele
        response = supabase.table("sped_analyses")\
            .select("*")\
            .eq("id", analysis_id)\
            .eq("user_id", current_user.id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Análise não encontrada.")
            
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyses")
async def list_analyses(limit: int = 20, offset: int = 0, current_user = Security(get_current_user)):
    """
    Lista o histórico das últimas análises realizadas pelo usuário logado.
    """
    try:
        response = supabase.table("sped_analyses")\
            .select("id, filename, cnpj, razao_social, uf, periodo_ini, periodo_fin, score, created_at")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
            
        return {
            "analyses": response.data,
            "total": len(response.data), # Simplificado para o exemplo
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
