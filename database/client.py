import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    Client = None

# Só inicializa se tiver as credenciais e o pacote instalado
def get_supabase_client() -> Client | None:
    if HAS_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Erro ao inicializar Supabase: {e}")
            return None
    return None

supabase: Client | None = get_supabase_client()
