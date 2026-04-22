# -*- coding: utf-8 -*-
"""
Comparador de períodos — analisa diferenças entre múltiplos arquivos SPED EFD.
Identifica variações significativas entre meses/trimestres.
"""
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from api.models.sped_file import AnalysisResult
from api.models.finding import Severity


class PeriodDivergence:
    """Representa uma divergência ou variação significativa entre períodos."""

    def __init__(
        self,
        field: str,
        description: str,
        periods: List[Tuple[str, Decimal]],
        variation_pct: float,
        severity: Severity = Severity.WARNING,
    ):
        self.field = field
        self.description = description
        self.periods = periods  # [(periodo, valor), ...]
        self.variation_pct = variation_pct
        self.severity = severity

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "description": self.description,
            "periods": [{"periodo": p, "valor": float(v)} for p, v in self.periods],
            "variation_pct": round(self.variation_pct, 2),
            "severity": self.severity.value,
        }


class ComparisonResult:
    """Resultado da comparação entre múltiplos períodos."""

    def __init__(self):
        self.periods: List[str] = []
        self.divergences: List[PeriodDivergence] = []
        self.score_evolution: List[Tuple[str, float]] = []
        self.summary: Dict[str, any] = {}

    def to_dict(self) -> dict:
        return {
            "periods": self.periods,
            "divergences": [d.to_dict() for d in self.divergences],
            "score_evolution": [{"periodo": p, "score": s} for p, s in self.score_evolution],
            "summary": self.summary,
            "total_divergences": len(self.divergences),
        }


# Limiar de variação que dispara alerta (30%)
VARIATION_THRESHOLD = 30.0

# Campos do E110 para comparar
E110_FIELDS = [
    ("VL_TOT_DEBITOS", "Total de Débitos do ICMS"),
    ("VL_TOT_CREDITOS", "Total de Créditos do ICMS"),
    ("VL_SLD_APURADO", "Saldo Devedor Apurado"),
    ("VL_ICMS_RECOLHER", "ICMS a Recolher"),
    ("VL_SLD_CREDOR_TRANSPORTAR", "Saldo Credor a Transportar"),
    ("DEB_ESP", "Débitos Especiais"),
]


class PeriodComparator:
    """Compara múltiplos AnalysisResult para identificar variações."""

    def __init__(self, analyses: List[AnalysisResult]):
        self.analyses = sorted(
            analyses,
            key=lambda a: a.file_info.periodo_ini or ""
        )

    def compare(self) -> ComparisonResult:
        """Executa a comparação completa."""
        result = ComparisonResult()
        result.periods = [self._format_period(a) for a in self.analyses]
        result.score_evolution = [(self._format_period(a), a.score) for a in self.analyses]

        # Comparar E110 entre períodos
        result.divergences.extend(self._compare_e110())

        # Comparar ICMS-ST (E210)
        result.divergences.extend(self._compare_e210())

        # Comparar score evolution
        result.divergences.extend(self._check_score_drops())

        # Summary
        result.summary = {
            "total_periods": len(self.analyses),
            "best_score": max(a.score for a in self.analyses),
            "worst_score": min(a.score for a in self.analyses),
            "avg_score": round(sum(a.score for a in self.analyses) / len(self.analyses), 1),
            "total_divergences": len(result.divergences),
        }

        return result

    def _compare_e110(self) -> List[PeriodDivergence]:
        """Compara campos do E110 entre períodos consecutivos."""
        divergences = []

        for field, label in E110_FIELDS:
            values = []
            for analysis in self.analyses:
                # Buscar E110 no parsed result (usar findings info para reconstruir)
                # Para a comparação, precisamos dos dados diretamente
                periodo = self._format_period(analysis)
                # Extrair do modelo via block_summaries (simplificação para v1)
                values.append((periodo, Decimal("0")))  # Placeholder

            # Verificar variação entre períodos consecutivos
            for i in range(1, len(values)):
                prev_periodo, prev_val = values[i - 1]
                curr_periodo, curr_val = values[i]

                if prev_val > 0:
                    variation = float(((curr_val - prev_val) / prev_val) * 100)
                    if abs(variation) > VARIATION_THRESHOLD:
                        severity = Severity.WARNING if abs(variation) < 80 else Severity.CRITICAL
                        divergences.append(PeriodDivergence(
                            field=field,
                            description=f"{label}: variação de {variation:+.1f}% entre {prev_periodo} e {curr_periodo}",
                            periods=[(prev_periodo, prev_val), (curr_periodo, curr_val)],
                            variation_pct=variation,
                            severity=severity,
                        ))

        return divergences

    def _compare_e210(self) -> List[PeriodDivergence]:
        """Compara ICMS-ST entre períodos."""
        return []  # TODO: Implementar quando tiver acesso completo ao parsed

    def _check_score_drops(self) -> List[PeriodDivergence]:
        """Verifica quedas bruscas no score de conformidade."""
        divergences = []
        for i in range(1, len(self.analyses)):
            prev = self.analyses[i - 1]
            curr = self.analyses[i]
            drop = prev.score - curr.score

            if drop > 20:
                divergences.append(PeriodDivergence(
                    field="SCORE",
                    description=(
                        f"Queda de {drop:.1f} pontos no score de conformidade: "
                        f"{prev.score:.1f}% → {curr.score:.1f}%"
                    ),
                    periods=[
                        (self._format_period(prev), Decimal(str(prev.score))),
                        (self._format_period(curr), Decimal(str(curr.score))),
                    ],
                    variation_pct=-drop,
                    severity=Severity.CRITICAL if drop > 40 else Severity.WARNING,
                ))

        return divergences

    @staticmethod
    def _format_period(analysis: AnalysisResult) -> str:
        """Formata o período de uma análise."""
        if analysis.file_info.periodo_ini:
            return analysis.file_info.periodo_ini.strftime("%m/%Y")
        return analysis.filename
