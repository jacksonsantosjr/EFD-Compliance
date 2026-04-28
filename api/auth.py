import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database.client import supabase

security = HTTPBearer()

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    """
    Verifica o token JWT do Supabase enviado pelo frontend.
    Retorna o objeto do usuário se válido.
    """
    token = auth.credentials
    try:
        # No Supabase Python SDK, usamos auth.get_user(token) para validar
        # Isso garante que o token não foi adulterado e pertence a um usuário ativo
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticação inválido ou expirado.",
            )
        return res.user
    except Exception as e:
        print(f"Erro na validação de token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais.",
        )

async def log_audit_event(user_id: str, action: str, target_id: str = None, details: dict = None):
    """
    Registra um evento de auditoria no Supabase.
    """
    try:
        payload = {
            "user_id": user_id,
            "action": action,
            "target_id": target_id,
            "details": details
        }
        supabase.table("audit_events").insert(payload).execute()
    except Exception as e:
        # Falha no log não deve travar a aplicação, mas deve ser registrada no console
        print(f"ERRO CRÍTICO: Falha ao registrar log de auditoria: {e}")
