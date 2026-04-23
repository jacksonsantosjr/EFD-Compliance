# -*- coding: utf-8 -*-
"""
Pydantic models para arquivo SPED e resultado de análise.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import date, datetime

from api.models.finding import Finding, BlockSummary


class SpedFileInfo(BaseModel):
    """Informações extraídas do registro 0000 do arquivo SPED."""
    cnpj: str = ""
    razao_social: str = ""
    uf: str = ""
    ie: str = ""
    cod_mun: str = ""
    periodo_ini: Optional[date] = None
    periodo_fin: Optional[date] = None
    perfil: str = ""  # A, B ou C
    cod_ver: str = ""  # Versão do layout
    ind_ativ: str = ""  # Indicador de atividade (0=Industrial, 1=Outros)
    total_linhas: int = 0
    tipo_arquivo: str = "EFD"  # EFD, ECD, ECF


class AnalysisResult(BaseModel):
    """Resultado completo de uma análise de arquivo SPED."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str = ""
    file_hash: str = ""
    file_info: SpedFileInfo = Field(default_factory=SpedFileInfo)
    total_registros: int = 0
    score: float = Field(0.0, ge=0.0, le=100.0, description="Score de conformidade 0-100%")
    findings: List[Finding] = Field(default_factory=list)
    block_summaries: Dict[str, BlockSummary] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    validator_version: str = "1.0.0"

    @property
    def findings_by_severity(self) -> Dict[str, List[Finding]]:
        """Agrupa achados por severidade."""
        result = {"critical": [], "warning": [], "info": []}
        for f in self.findings:
            result[f.severity.value].append(f)
        return result

    @property
    def total_critical(self) -> int:
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def total_warnings(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def total_info(self) -> int:
        return sum(1 for f in self.findings if f.severity == "info")


class AnalysisSummary(BaseModel):
    """Resumo de uma análise para listagem (histórico)."""
    id: str
    filename: str
    cnpj: str
    razao_social: str
    uf: str
    periodo: str
    score: float
    total_findings: int
    total_critical: int
    created_at: datetime
