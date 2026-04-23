# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
import uuid

from api.models.sped_file import AnalysisResult, SpedFileInfo
from api.models.finding import Finding, Severity, Category
from parser.ecd_parser import EcdParseResult
from parser.ecf_parser import EcfParseResult

class CrossEcdEcfValidator:
    """Orquestrador do Cruzamento de Auditoria entre ECD e ECF (Malha Fina Integrada)."""
    
    def __init__(self, parsed_ecd: EcdParseResult, parsed_ecf: EcfParseResult):
        self.ecd = parsed_ecd
        self.ecf = parsed_ecf
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
            impact="Risco alto de autuação via Malha Fina Eletrônica (Divergência Contábil/Fiscal).",
            recomendation="Retifique a obrigação divergente ou justifique por meio de lançamento extemporâneo/ajuste."
        )
        self.findings.append(issue)
        
        if level == "error":
            self.score -= 5.0
        elif level == "warning":
            self.score -= 2.0

    def _cross_plano_de_contas(self):
        """
        Garante que o Plano de Contas entregue na ECD (I050) existe na ECF (J050)
        com as mesmas características, especialmente para contas analíticas.
        """
        i050_regs = self.ecd.get_registros("I050")
        j050_regs = self.ecf.get_registros("J050")
        
        # Mapeia as contas analíticas da ECF (J050)
        # J050 layout usual: J050|DT_ALT|COD_NAT|IND_CTA|NIVEL|COD_CTA|COD_CTA_SUP|CTA|
        ecf_contas = {}
        for r in j050_regs:
            cod = r.campos_raw[5] if len(r.campos_raw) > 5 else None
            ind_cta = r.campos_raw[3].upper() if len(r.campos_raw) > 3 else None
            desc = r.campos_raw[7] if len(r.campos_raw) > 7 else None
            if cod and ind_cta == "A":
                ecf_contas[cod] = desc
                
        # Valida contra o I050 da ECD
        # I050 layout usual: I050|DT_ALT|COD_NAT|IND_CTA|NIVEL|COD_CTA|COD_CTA_SUP|CTA|
        for r in i050_regs:
            cod = r.campos_raw[5] if len(r.campos_raw) > 5 else None
            ind_cta = r.campos_raw[3].upper() if len(r.campos_raw) > 3 else None
            desc = r.campos_raw[7] if len(r.campos_raw) > 7 else None
            
            if cod and ind_cta == "A":
                if cod not in ecf_contas:
                    self.add_issue(
                        code="ECF-CROSS-001",
                        title="Conta Existente na ECD Omitida na ECF",
                        description=f"A conta analítica '{cod} - {desc}' está declarada na ECD, mas desapareceu do plano de contas da ECF (J050).",
                        level="error",
                        category="Compliance",
                        registro="J050"
                    )

    def _cross_saldos_patrimoniais(self):
        """
        Compara o Saldo Final apurado na ECD (I155) com os saldos transportados para a ECF (K155).
        As contas com saldo diferente de zero na ECD precisam espelhar esse saldo na ECF.
        """
        i155_regs = self.ecd.get_registros("I155")
        k155_regs = self.ecf.get_registros("K155")
        
        # Mapa de saldos finais da ECD
        # I155: |I155|COD_CTA|COD_CCUS|VL_SLD_INI|IND_DC_INI|VL_DEB|VL_CRED|VL_SLD_FIN|IND_DC_FIN|
        ecd_saldos = {}
        for r in i155_regs:
            cod = r.campos_raw[1] if len(r.campos_raw) > 1 else None
            vl_fin = float(r.campos_raw[7].replace(",", ".")) if len(r.campos_raw) > 7 and r.campos_raw[7] else 0.0
            ind_fin = r.campos_raw[8].upper() if len(r.campos_raw) > 8 else "D"
            if cod:
                ecd_saldos[cod] = {"valor": vl_fin, "ind": ind_fin}
                
        # Valida contra K155 da ECF
        # K155: |K155|COD_CTA|COD_CCUS|VL_SLD_INI|IND_VL_SLD_INI|VL_DEB|VL_CRED|VL_SLD_FIN|IND_VL_SLD_FIN|
        ecf_saldos = {}
        for r in k155_regs:
            cod = r.campos_raw[1] if len(r.campos_raw) > 1 else None
            vl_fin = float(r.campos_raw[7].replace(",", ".")) if len(r.campos_raw) > 7 and r.campos_raw[7] else 0.0
            ind_fin = r.campos_raw[8].upper() if len(r.campos_raw) > 8 else "D"
            if cod:
                ecf_saldos[cod] = {"valor": vl_fin, "ind": ind_fin}
                
        for cod, saldo_ecd in ecd_saldos.items():
            if saldo_ecd["valor"] > 0:
                saldo_ecf = ecf_saldos.get(cod)
                if not saldo_ecf:
                    self.add_issue(
                        code="ECF-CROSS-002",
                        title="Saldo Final ECD ausente na ECF (K155)",
                        description=f"A conta {cod} possui saldo final de R$ {saldo_ecd['valor']:.2f} ({saldo_ecd['ind']}) na ECD, mas está ausente na movimentação (K155) da ECF.",
                        level="error",
                        category="Matemática",
                        registro="K155"
                    )
                else:
                    if abs(saldo_ecd["valor"] - saldo_ecf["valor"]) > 0.05 or saldo_ecd["ind"] != saldo_ecf["ind"]:
                        self.add_issue(
                            code="ECF-CROSS-003",
                            title="Divergência de Saldo ECD vs ECF",
                            description=f"A conta {cod} terminou a ECD com R$ {saldo_ecd['valor']:.2f} ({saldo_ecd['ind']}), mas a ECF declara R$ {saldo_ecf['valor']:.2f} ({saldo_ecf['ind']}).",
                            level="error",
                            category="Matemática",
                            registro="K155"
                        )

    async def validate(self) -> AnalysisResult:
        """Executa a rotina de cruzamento entre os dois arquivos processados."""
        
        self._cross_plano_de_contas()
        self._cross_saldos_patrimoniais()
        
        self.score = max(0.0, min(100.0, self.score))
        
        # A informação principal para o header do result será da ECF, pois é a declaração fim.
        file_info = SpedFileInfo(
            cnpj=self.ecf.file_info.cnpj,
            razao_social=self.ecf.file_info.nome,
            uf=self.ecf.file_info.uf,
            periodo_ini=self.ecf.file_info.dt_ini,
            periodo_fin=self.ecf.file_info.dt_fin,
            total_linhas=self.ecd.total_registros + self.ecf.total_registros,
            tipo_arquivo="CRUZAMENTO_ECD_ECF"
        )
        
        return AnalysisResult(
            id=str(uuid.uuid4()),
            filename="", 
            file_hash="",
            file_info=file_info,
            score=self.score,
            findings=self.findings,
            total_registros=self.ecd.total_registros + self.ecf.total_registros,
            created_at=datetime.utcnow()
        )
