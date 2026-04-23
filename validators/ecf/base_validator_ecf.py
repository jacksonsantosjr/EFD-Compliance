# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
import uuid

from api.models.sped_file import AnalysisResult, SpedFileInfo
from api.models.finding import Finding, Severity, Category

from parser.ecf_parser import EcfParseResult
from validators.ecf.referencial_validator_ecf import ReferencialValidatorECF
from validators.ecf.lalur_validator_ecf import LalurValidatorECF
from validators.ecf.quality_validator_ecf import QualityValidatorECF

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
            block=registro[0] if registro else "0",
            impact="Compromete a integridade fiscal e o mérito da apuração do IRPJ/CSLL.",
            recommendation="Revise a classificação contábil e as regras de apuração do Lucro Real/Presumido."
        )
        self.findings.append(issue)
        
        if level == "error":
            self.score -= 5.0
        elif level == "warning":
            self.score -= 2.0
            
    async def validate(self) -> AnalysisResult:
        """Executa todas as esteiras de validação da ECF."""
        
        # 1. Validação do Plano de Contas Referencial (Blocos J e K)
        ref_validator = ReferencialValidatorECF(self)
        ref_validator.validate_all()
        
        # 2. Validação do LALUR/LACS (Blocos M e N)
        lalur_validator = LalurValidatorECF(self)
        lalur_validator.validate_all()
        
        # 3. Validação de Qualidade e Compliance (Fase 9)
        quality_validator = QualityValidatorECF(self)
        quality_validator.validate_all()
        
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
