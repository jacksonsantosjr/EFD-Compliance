# -*- coding: utf-8 -*-
"""
Validador Base — Orquestrador principal.
Coordena os validadores matemáticos, cruzamento e regras por UF.
Calcula o score de conformidade.
"""
from typing import List, Dict
from decimal import Decimal

from api.models.finding import Finding, Severity, BlockSummary
from api.models.sped_file import AnalysisResult, SpedFileInfo as PydanticSpedFileInfo
from parser.sped_parser import SpedParseResult
from validators.math_validator import MathValidator
from validators.cross_block_validator import CrossBlockValidator
from validators.cadastral_validator import CadastralValidator
from validators.uf_rules import get_uf_rules, has_uf_rules
from knowledge_base.loader import get_loader


# Nomes dos blocos
BLOCK_NAMES = {
    "0": "Abertura e Cadastros",
    "B": "Apuração ISS (DES-IF)",
    "C": "Documentos Fiscais — Mercadorias",
    "D": "Documentos Fiscais — Serviços/Transporte",
    "E": "Apuração ICMS/IPI",
    "G": "CIAP (Crédito Ativo Permanente)",
    "H": "Inventário Físico",
    "K": "Produção e Estoque",
    "1": "Informações Complementares",
    "9": "Controle e Encerramento",
}


class BaseValidator:
    """
    Orquestrador principal de validação.
    Coordena Math, CrossBlock e UF Rules, e calcula o score final.
    """

    def __init__(self, parsed: SpedParseResult):
        self.parsed = parsed
        self.findings: List[Finding] = []
        self.block_summaries: Dict[str, BlockSummary] = {}

    async def validate(self) -> AnalysisResult:
        """Executa toda a pipeline de validação e retorna o AnalysisResult."""
        self.findings = []

        # 1. Validações matemáticas
        math_val = MathValidator(self.parsed)
        self.findings.extend(math_val.validate_all())

        # 2. Cruzamentos entre blocos
        cross_val = CrossBlockValidator(self.parsed)
        self.findings.extend(cross_val.validate_all())
        
        # 3. Validação Cadastral (Fornecedores 0150)
        cadastral_val = CadastralValidator(self.parsed)
        cadastral_findings = await cadastral_val.validate_async()
        self.findings.extend(cadastral_findings)

        # 4. Regras específicas da UF
        uf = self.parsed.file_info.uf
        if uf:
            uf_rules = get_uf_rules(uf)
            if uf_rules:
                self.findings.extend(uf_rules.validate(self.parsed))
            else:
                # Registrar que não há regras específicas
                loader = get_loader()
                if not loader.has_tabela_511(uf):
                    self.findings.append(Finding(
                        block="0", register="0000", severity=Severity.INFO,
                        code="UF-INFO-001",
                        title=f"UF {uf} sem Tabela 5.1.1 ou regras específicas",
                        description=(
                            f"A UF {uf} não possui Tabela 5.1.1 publicada "
                            f"ou módulo de regras implementado. "
                            f"Apenas validações gerais (Guia Prático) foram aplicadas."
                        ),
                        recommendation="Validações específicas da UF serão implementadas em versões futuras."
                    ))

        # 5. Montar resumos por bloco
        self._build_block_summaries()

        # 6. Calcular score
        score = self._calculate_score()

        # 7. Montar resultado
        info = self.parsed.file_info
        result = AnalysisResult(
            filename=self.parsed.filename,
            file_hash=self.parsed.file_hash,
            file_info=PydanticSpedFileInfo(
                cnpj=info.cnpj,
                razao_social=info.nome,
                uf=info.uf,
                ie=info.ie,
                cod_mun=info.cod_mun,
                periodo_ini=info.dt_ini,
                periodo_fin=info.dt_fin,
                perfil=info.ind_perfil,
                cod_ver=info.cod_ver,
                ind_ativ=info.ind_ativ,
                total_linhas=info.total_linhas,
            ),
            total_registros=self.parsed.total_registros,
            score=score,
            findings=self.findings,
            block_summaries=self.block_summaries,
        )

        return result

    def _build_block_summaries(self):
        """Constrói resumo de cada bloco."""
        self.block_summaries = {}

        for block_code, block_name in BLOCK_NAMES.items():
            block_regs = self.parsed.get_bloco(block_code)
            total_records = sum(len(regs) for regs in block_regs.values())

            # Contar achados por severidade para este bloco
            block_findings = [f for f in self.findings
                              if f.block == block_code or f.block.startswith(f"{block_code}×")]
            critical = sum(1 for f in block_findings if f.severity == Severity.CRITICAL)
            warnings = sum(1 for f in block_findings if f.severity == Severity.WARNING)
            infos = sum(1 for f in block_findings if f.severity == Severity.INFO)

            # Determinar status
            if critical > 0:
                status = "critical"
            elif warnings > 0:
                status = "warning"
            else:
                status = "ok"

            self.block_summaries[block_code] = BlockSummary(
                block=block_code,
                block_name=block_name,
                status=status,
                total_records=total_records,
                findings_critical=critical,
                findings_warning=warnings,
                findings_info=infos,
            )

    def _calculate_score(self) -> float:
        """
        Calcula score de conformidade (0-100%).
        
        Metodologia:
        - Cada achado CRITICAL reduz 10 pontos
        - Cada achado WARNING reduz 3 pontos
        - Achados INFO não reduzem
        - Score mínimo: 0
        """
        total_critical = sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
        total_warnings = sum(1 for f in self.findings if f.severity == Severity.WARNING)

        deducao = (total_critical * 10) + (total_warnings * 3)
        score = max(0.0, 100.0 - deducao)

        return round(score, 1)
