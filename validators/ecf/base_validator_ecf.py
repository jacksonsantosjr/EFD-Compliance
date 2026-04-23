# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
import uuid

from api.models.sped_file import AnalysisResult, SpedFileInfo
from api.models.finding import Finding, Severity, Category

from parser.ecf_parser import EcfParseResult

class ECFValidator:
    """Orquestrador das validações da Escrituração Contábil Fiscal (ECF)."""
    
    def __init__(self, parsed_data: EcfParseResult):
        self.parsed = parsed_data
        self.findings: List[Finding] = []
        self.score = 100.0

    def add_issue(self, code: str, title: str, description: str, 
                  level: str, category: str, 
                  registro: str, details: str = None):
        
        severity_map = {
            "error": Severity.CRITICAL,
            "warning": Severity.WARNING,
            "info": Severity.INFO
        }
        
        issue = Finding(
            code=code,
            title=title,
            description=description,
            severity=severity_map.get(level, Severity.INFO),
            category=Category.COMPLIANCE if category == "Compliance" else Category.MATH,
            registro=registro,
            impact="Compromete a integridade fiscal do arquivo ECF.",
            recomendation="Ajuste as informações contábeis/fiscais declaradas."
        )
        self.findings.append(issue)
        
        if level == "error":
            self.score -= 5.0
        elif level == "warning":
            self.score -= 2.0
            
    async def validate(self) -> AnalysisResult:
        """Executa todas as esteiras de validação da ECF."""
        
        # Etapas futuras (LALUR/LACS e Referencial) serão chamadas aqui
        
        # Garantir limite do score
        self.score = max(0.0, min(100.0, self.score))
        
        file_info = SpedFileInfo(
            cnpj=self.parsed.file_info.cnpj,
            razao_social=self.parsed.file_info.nome,
            uf=self.parsed.file_info.uf,
            periodo_ini=self.parsed.file_info.dt_ini,
            periodo_fin=self.parsed.file_info.dt_fin,
            total_linhas=self.parsed.file_info.total_linhas,
            tipo_arquivo="ECF"
        )
        
        return AnalysisResult(
            id=str(uuid.uuid4()),
            filename="", 
            file_hash="",
            file_info=file_info,
            score=self.score,
            findings=self.findings,
            total_registros=self.parsed.total_registros,
            created_at=datetime.utcnow()
        )
