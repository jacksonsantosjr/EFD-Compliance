import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Só inicializa se tiver as credenciais
def get_supabase_client() -> Client | None:
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Erro ao inicializar Supabase: {e}")
            return None
    return None

supabase: Client | None = get_supabase_client()
