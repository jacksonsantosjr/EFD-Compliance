# -*- coding: utf-8 -*-
import asyncio
import httpx
import re
import time
from typing import Optional, Dict, Any, List

COOLDOWN_DURATION = 60.0  # 60 segundos de punição se der erro 429

class CnpjApi:
    def __init__(self, api_id: str, name: str, url_template: str, rate_limit: int):
        self.api_id = api_id
        self.name = name
        self.url_template = url_template
        self.rate_limit = rate_limit
    
    def build_url(self, cnpj: str) -> str:
        return self.url_template.replace("{cnpj}", cnpj)

API_LIST = [
    CnpjApi("opencnpj_org", "OpenCNPJ.org", "https://api.opencnpj.org/{cnpj}", 100),
    CnpjApi("opencnpj_com", "OpenCNPJ.com", "https://kitana.opencnpj.com/cnpj/{cnpj}", 100),
    CnpjApi("minhareceita", "MinhaReceita", "https://minhareceita.org/{cnpj}", 50),
    CnpjApi("brasilapi", "BrasilAPI", "https://brasilapi.com.br/api/cnpj/v1/{cnpj}", 30),
    CnpjApi("receitaws", "ReceitaWS", "https://receitaws.com.br/v1/cnpj/{cnpj}", 3),
    CnpjApi("cnpja", "CNPJá", "https://open.cnpja.com/office/{cnpj}", 5),
]

class CnpjService:
    def __init__(self):
        self.current_api_index = 0
        self.cooldowns: Dict[str, float] = {}
        # Cliente HTTP que ignora SSL cert verification, simulando o rejectUnauthorized=false do NodeJS
        self.client = httpx.AsyncClient(verify=False, timeout=15.0)

    async def close(self):
        await self.client.aclose()

    def get_next_available_api(self) -> CnpjApi:
        now = time.time()
        total_apis = len(API_LIST)

        for attempt in range(total_apis):
            idx = (self.current_api_index + attempt) % total_apis
            api = API_LIST[idx]
            cooldown_until = self.cooldowns.get(api.api_id, 0.0)

            if now >= cooldown_until:
                self.current_api_index = (idx + 1) % total_apis
                return api

        # Se todas estiverem em cooldown, escolhe a que terminará primeiro
        shortest = None
        min_remaining = float('inf')
        for api in API_LIST:
            remaining = self.cooldowns.get(api.api_id, 0.0) - now
            if remaining < min_remaining:
                shortest = api
                min_remaining = remaining
        
        # Pode forçar uma espera se quisermos, mas o round-robin original retorna a melhor
        return shortest or API_LIST[0]

    def put_api_in_cooldown(self, api_id: str):
        self.cooldowns[api_id] = time.time() + COOLDOWN_DURATION
        print(f"⏸️  [{api_id}] em cooldown por {COOLDOWN_DURATION}s")

    def clean_cnpj(self, raw_cnpj: str) -> str:
        return re.sub(r'\D', '', str(raw_cnpj)).zfill(14)

    def normalize_data(self, data: Any, api_id: str) -> Dict[str, str]:
        fields = {
            "cnpj": "",
            "nome": "",
            "situacao": ""
        }
        
        if not isinstance(data, dict):
            return fields

        if api_id in ("opencnpj_org", "minhareceita", "brasilapi"):
            fields["nome"] = data.get("razao_social", "")
            fields["situacao"] = data.get("descricao_situacao_cadastral", "")
        elif api_id == "opencnpj_com":
            d = data.get("data", data)
            fields["nome"] = d.get("razaoSocial", "")
            fields["situacao"] = d.get("situacaoCadastral", "")
        elif api_id == "receitaws":
            fields["nome"] = data.get("nome", "")
            fields["situacao"] = data.get("situacao", "")
        elif api_id == "cnpja":
            company = data.get("company", {})
            status = data.get("status", {})
            fields["nome"] = company.get("name", "")
            fields["situacao"] = status.get("text", "")
            
        return fields

    async def query_with_retry(self, url: str, retries: int = 2, delay_ms: int = 1000) -> Optional[Dict]:
        for attempt in range(1, retries + 1):
            try:
                response = await self.client.get(url, headers={"Accept": "application/json"})
                if response.status_code == 404:
                    return None
                if response.status_code in (403, 429):
                    response.raise_for_status()
                if response.status_code >= 500:
                    response.raise_for_status()
                    
                # Muitas vezes APIs retornam 200 OK mas com html ou string vazia
                if not response.content:
                    return None
                    
                return response.json()
            except httpx.HTTPStatusError as err:
                status = err.response.status_code
                if status in (403, 429):
                    raise err
                if attempt == retries:
                    raise err
                await asyncio.sleep((delay_ms * attempt) / 1000.0)
            except Exception as err:
                if attempt == retries:
                    raise err
                await asyncio.sleep((delay_ms * attempt) / 1000.0)
        return None

    async def query_cnpj(self, raw_cnpj: str) -> Dict[str, str]:
        cnpj = self.clean_cnpj(raw_cnpj)
        total_apis = len(API_LIST)

        for attempt in range(total_apis):
            api = self.get_next_available_api()

            # Se a API que pegamos ainda estiver em cooldown, significa que estouramos todas as APIs
            # Aguardamos um pouco antes de tentar (o que sobrar de cooldown)
            now = time.time()
            until = self.cooldowns.get(api.api_id, 0.0)
            if until > now:
                wait_time = until - now
                print(f"⏳ Aguardando {wait_time:.1f}s para usar {api.name} (todas as APIs esgotadas)")
                await asyncio.sleep(min(wait_time, 5.0)) # Espera max 5 segundos e tenta de novo

            try:
                url = api.build_url(cnpj)
                data = await self.query_with_retry(url)

                if data and not (isinstance(data, dict) and data.get("success") is False):
                    normalized = self.normalize_data(data, api.api_id)
                    
                    clean_name = re.sub(r'[^\x20-\x7EÀ-ÿ]', '', str(normalized.get("nome", ""))).strip()
                    
                    if clean_name:
                        normalized["nome"] = clean_name
                        normalized["cnpj"] = cnpj
                        normalized["status"] = "success"
                        normalized["api"] = api.name
                        return normalized
                    
            except httpx.HTTPStatusError as err:
                status = err.response.status_code
                print(f"❌ [{api.name}] {cnpj}: Status {status}")
                if status in (403, 429) or status >= 500:
                    self.put_api_in_cooldown(api.api_id)
            except Exception as err:
                print(f"❌ [{api.name}] {cnpj}: {str(err)}")

        return {
            "cnpj": cnpj,
            "status": "error",
            "api": "none",
            "error": "Todas as APIs falharam para este CNPJ"
        }
