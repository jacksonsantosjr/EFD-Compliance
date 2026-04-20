# -*- coding: utf-8 -*-
"""
Loader da Base de Conhecimento.
Carrega tabelas de referência (5.1.1, CFOP, NCM, etc.) para uso nos validadores.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import re

from api.config import KNOWLEDGE_BASE_DIR


class TabelaEntry:
    """Entrada de uma tabela de referência."""
    def __init__(self, codigo: str, descricao: str, **kwargs):
        self.codigo = codigo
        self.descricao = descricao
        self.extras = kwargs

    def __repr__(self):
        return f"<TabelaEntry {self.codigo}: {self.descricao[:50]}>"


class KnowledgeBaseLoader:
    """
    Carregador lazy da base de conhecimento.
    Carrega tabelas em memória sob demanda e mantém cache.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or KNOWLEDGE_BASE_DIR
        self._cache: Dict[str, any] = {}

    def get_tabela_511(self, uf: str) -> Dict[str, TabelaEntry]:
        """
        Carrega e retorna a Tabela 5.1.1 de uma UF específica.
        A tabela mapeia códigos de ajuste para descrição e campo do E110.
        
        O 4º caractere do código determina o campo:
          0 = VL_AJ_DEBITOS (campo 03)
          1 = VL_ESTORNOS_CRED (campo 05)
          2 = VL_AJ_CREDITOS (campo 07)
          3 = VL_ESTORNOS_DEB (campo 09)
          4 = VL_TOT_DED (campo 12)
          5 = DEB_ESP (campo 15)
          9 = Outros ajustes
        """
        cache_key = f"tabela_511_{uf}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        tabela = {}
        tabela_dir = self.base_dir / "tabelas_511"

        # Tentar diferentes padrões de nome
        patterns = [
            f"Tabela 5.1.1 - {uf}*.txt",
            f"tabela_511_{uf.lower()}.txt",
            f"*5.1.1*{uf}*",
        ]

        arquivo = None
        for pattern in patterns:
            matches = list(tabela_dir.glob(pattern))
            if matches:
                arquivo = matches[0]
                break

        if arquivo and arquivo.exists():
            tabela = self._parse_tabela_511(arquivo)

        self._cache[cache_key] = tabela
        return tabela

    def _parse_tabela_511(self, filepath: Path) -> Dict[str, TabelaEntry]:
        """Parseia arquivo da Tabela 5.1.1 (formato TXT tabulado)."""
        tabela = {}
        try:
            content = filepath.read_text(encoding="latin-1")
            for linha in content.strip().split("\n"):
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                # Formato esperado: CÓDIGO|DESCRIÇÃO ou CÓDIGO\tDESCRIÇÃO
                partes = re.split(r'[|\t]', linha, maxsplit=1)
                if len(partes) >= 2:
                    codigo = partes[0].strip()
                    descricao = partes[1].strip()
                    # Extrair campo do E110 pelo 4º caractere
                    campo_e110 = self._get_campo_e110(codigo)
                    tabela[codigo] = TabelaEntry(
                        codigo=codigo,
                        descricao=descricao,
                        campo_e110=campo_e110,
                    )
        except Exception:
            pass
        return tabela

    @staticmethod
    def _get_campo_e110(codigo_ajuste: str) -> str:
        """
        Determina qual campo do E110 é alimentado pelo código de ajuste.
        Baseado no 4º caractere do código (ex: SP020207 → 4º char = '2' = crédito).
        """
        if len(codigo_ajuste) < 4:
            return "DESCONHECIDO"

        quarto_char = codigo_ajuste[3]
        mapa = {
            "0": "VL_AJ_DEBITOS",        # Campo 03 do E110
            "1": "VL_ESTORNOS_CRED",      # Campo 05 do E110
            "2": "VL_AJ_CREDITOS",        # Campo 07 do E110
            "3": "VL_ESTORNOS_DEB",       # Campo 09 do E110
            "4": "VL_TOT_DED",            # Campo 12 do E110
            "5": "DEB_ESP",               # Campo 15 do E110
            "9": "OUTROS_AJUSTES",        # Informativo/outros
        }
        return mapa.get(quarto_char, "DESCONHECIDO")

    def get_tabela_cfop(self) -> Dict[str, str]:
        """Carrega tabela de CFOPs com descrição."""
        if "cfop" in self._cache:
            return self._cache["cfop"]

        tabela = {}
        cfop_file = self.base_dir / "tabela_cfop.txt"
        if not cfop_file.exists():
            # Tentar também o nome do arquivo fornecido
            cfop_matches = list(self.base_dir.glob("*CFOP*"))
            if cfop_matches:
                cfop_file = cfop_matches[0]

        if cfop_file.exists():
            try:
                content = cfop_file.read_text(encoding="latin-1")
                for linha in content.strip().split("\n"):
                    partes = re.split(r'[|\t;]', linha.strip(), maxsplit=1)
                    if len(partes) >= 2:
                        tabela[partes[0].strip()] = partes[1].strip()
            except Exception:
                pass

        self._cache["cfop"] = tabela
        return tabela

    def has_tabela_511(self, uf: str) -> bool:
        """Verifica se existe Tabela 5.1.1 para a UF."""
        tabela = self.get_tabela_511(uf)
        return len(tabela) > 0

    def get_campo_e110_for_code(self, codigo_ajuste: str) -> str:
        """Retorna o campo do E110 alimentado por um código de ajuste."""
        return self._get_campo_e110(codigo_ajuste)

    def clear_cache(self):
        """Limpa o cache de tabelas."""
        self._cache.clear()


# Instância singleton do loader
_loader_instance: Optional[KnowledgeBaseLoader] = None


def get_loader() -> KnowledgeBaseLoader:
    """Retorna instância singleton do loader."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = KnowledgeBaseLoader()
    return _loader_instance
