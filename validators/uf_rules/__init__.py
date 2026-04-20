# -*- coding: utf-8 -*-
"""
Loader dinâmico de regras por UF.
Carrega automaticamente o módulo da UF identificada no arquivo SPED.
"""
from typing import Optional, Dict, Type
from validators.uf_rules.base_uf import BaseUFRules
from validators.uf_rules.sp import SPRules


# Registry de UFs implementadas
_UF_REGISTRY: Dict[str, Type[BaseUFRules]] = {
    "SP": SPRules,
}


def get_uf_rules(uf: str) -> Optional[BaseUFRules]:
    """
    Retorna instância das regras da UF, ou None se não houver regras específicas.
    """
    rules_class = _UF_REGISTRY.get(uf.upper())
    if rules_class:
        return rules_class()
    return None


def has_uf_rules(uf: str) -> bool:
    """Verifica se existe módulo de regras para a UF."""
    return uf.upper() in _UF_REGISTRY


def list_implemented_ufs() -> list:
    """Lista as UFs com implementação de regras específicas."""
    return list(_UF_REGISTRY.keys())
