# -*- coding: utf-8 -*-
"""
Pydantic models para achados de validação (Findings).
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime


class Severity(str, Enum):
    """Níveis de severidade dos achados."""
    CRITICAL = "critical"    # ❌ Erro grave que pode causar autuação
    WARNING = "warning"      # ⚠️ Inconsistência que merece atenção
    INFO = "info"            # ℹ️ Informação útil ou recomendação


class Finding(BaseModel):
    """Achado de validação — resultado de uma regra aplicada ao arquivo SPED."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    block: str = Field(..., description="Bloco do SPED (0, B, C, D, E, G, H, K, 1, 9)")
    register: str = Field(..., description="Registro (ex: E110, G125, C190)")
    severity: Severity = Field(..., description="Nível de severidade")
    code: str = Field(..., description="Código único do achado (ex: E110-MATH-001)")
    title: str = Field(..., description="Título resumido do achado")
    description: str = Field(..., description="Descrição detalhada")
    expected_value: Optional[str] = Field(None, description="Valor esperado")
    actual_value: Optional[str] = Field(None, description="Valor encontrado")
    legal_reference: Optional[str] = Field(None, description="Referência legal/normativa")
    recommendation: str = Field("", description="Ação corretiva sugerida")


class BlockSummary(BaseModel):
    """Resumo de validação de um bloco."""
    block: str
    block_name: str
    status: str = Field(..., description="ok, warning, critical")
    total_records: int = 0
    findings_critical: int = 0
    findings_warning: int = 0
    findings_info: int = 0

    @property
    def total_findings(self) -> int:
        return self.findings_critical + self.findings_warning + self.findings_info
