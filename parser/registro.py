# -*- coding: utf-8 -*-
"""
Classe base para registros do SPED EFD.
Cada registro é uma linha do arquivo TXT delimitada por pipe (|).
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal, InvalidOperation
from datetime import date


class Registro:
    """
    Representa um registro genérico do SPED EFD.
    
    O formato de cada linha é:  |REG|campo1|campo2|...|campoN|
    """

    # Mapeamento de campos: nome -> índice (sobrescrito pelas subclasses)
    CAMPOS: Dict[str, int] = {}

    def __init__(self, linha: str, numero_linha: int = 0):
        self.linha_raw = linha.strip()
        self.numero_linha = numero_linha
        self.campos_raw: List[str] = self._parse_linha(self.linha_raw)
        self.reg: str = self.campos_raw[0] if self.campos_raw else ""

    @staticmethod
    def _parse_linha(linha: str) -> List[str]:
        """
        Parseia uma linha do SPED EFD.
        Formato: |REG|campo1|campo2|...|campoN|
        Remove os pipes iniciais e finais.
        """
        if not linha:
            return []
        # Remove pipe inicial e final
        linha = linha.strip("|")
        return linha.split("|")

    def get_campo(self, nome: str) -> str:
        """Retorna o valor de um campo pelo nome."""
        idx = self.CAMPOS.get(nome)
        if idx is None:
            return ""
        if idx < len(self.campos_raw):
            return self.campos_raw[idx]
        return ""

    def get_campo_decimal(self, nome: str) -> Decimal:
        """Retorna o valor de um campo como Decimal."""
        valor = self.get_campo(nome)
        if not valor:
            return Decimal("0")
        try:
            # SPED usa vírgula como separador decimal
            valor = valor.replace(",", ".")
            return Decimal(valor)
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def get_campo_int(self, nome: str) -> int:
        """Retorna o valor de um campo como inteiro."""
        valor = self.get_campo(nome)
        if not valor:
            return 0
        try:
            return int(valor)
        except ValueError:
            return 0

    def get_campo_date(self, nome: str) -> Optional[date]:
        """Retorna o valor de um campo como date (formato DDMMYYYY)."""
        valor = self.get_campo(nome)
        if not valor or len(valor) != 8:
            return None
        try:
            return date(
                year=int(valor[4:8]),
                month=int(valor[2:4]),
                day=int(valor[0:2])
            )
        except (ValueError, IndexError):
            return None

    def total_campos(self) -> int:
        """Retorna a quantidade de campos no registro."""
        return len(self.campos_raw)

    def __repr__(self) -> str:
        return f"<Registro {self.reg} linha={self.numero_linha} campos={self.total_campos()}>"

    def to_dict(self) -> Dict[str, Any]:
        """Converte o registro para dicionário usando o mapeamento CAMPOS."""
        result = {"REG": self.reg, "_linha": self.numero_linha}
        for nome, idx in self.CAMPOS.items():
            if idx < len(self.campos_raw):
                result[nome] = self.campos_raw[idx]
            else:
                result[nome] = ""
        return result
