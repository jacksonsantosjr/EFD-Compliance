# -*- coding: utf-8 -*-
"""
Pydantic models para comparação entre períodos.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class PeriodDivergence(BaseModel):
    """Divergência encontrada entre dois períodos consecutivos."""
    field: str = Field(..., description="Campo divergente (ex: VL_SLD_CREDOR_TRANSPORTAR)")
    register: str = Field(..., description="Registro (ex: E110)")
    period_a_value: str = ""
    period_b_value: str = ""
    description: str = ""
    severity: str = "warning"


class ComparisonResult(BaseModel):
    """Resultado da comparação entre múltiplos arquivos SPED."""
    id: str
    analysis_ids: List[str] = Field(default_factory=list)
    periods: List[str] = Field(default_factory=list)
    divergences: List[PeriodDivergence] = Field(default_factory=list)
    total_divergences: int = 0
    continuity_score: float = Field(0.0, ge=0.0, le=100.0)
