# -*- coding: utf-8 -*-
"""
Interface base para regras específicas por UF.
Cada UF implementa esta interface com suas regras tributárias específicas.
"""
from abc import ABC, abstractmethod
from typing import List
from parser.sped_parser import SpedParseResult
from api.models.finding import Finding


class BaseUFRules(ABC):
    """Interface base que cada módulo de UF deve implementar."""

    @property
    @abstractmethod
    def uf(self) -> str:
        """Sigla da UF (ex: 'SP', 'MG')."""
        ...

    @property
    @abstractmethod
    def nome(self) -> str:
        """Nome completo da UF."""
        ...

    @abstractmethod
    def validate(self, parsed: SpedParseResult) -> List[Finding]:
        """Executa todas as validações específicas da UF."""
        ...

    @abstractmethod
    def validate_e111_codes(self, parsed: SpedParseResult) -> List[Finding]:
        """Valida os códigos de ajuste E111 contra a Tabela 5.1.1 da UF."""
        ...

    @abstractmethod
    def validate_difal(self, parsed: SpedParseResult) -> List[Finding]:
        """Valida obrigações de DIFAL (EC 87/2015)."""
        ...

    @abstractmethod
    def get_aliquota_interna(self, ncm: str) -> float:
        """Retorna a alíquota interna do ICMS para um NCM na UF."""
        ...

    def validate_bloco_k_obrigatoriedade(self, parsed: SpedParseResult) -> List[Finding]:
        """Verifica obrigatoriedade do Bloco K com base no CNAE."""
        return []

    def validate_bloco_h_obrigatoriedade(self, parsed: SpedParseResult) -> List[Finding]:
        """Verifica obrigatoriedade do inventário (H005)."""
        return []
