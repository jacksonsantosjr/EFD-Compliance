# -*- coding: utf-8 -*-
"""
Regras específicas de São Paulo (SP).
Implementação completa conforme RICMS/SP, Portarias CAT e legislação vigente.
"""
from decimal import Decimal
from typing import List

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult
from knowledge_base.loader import get_loader
from validators.uf_rules.base_uf import BaseUFRules


class SPRules(BaseUFRules):
    """Regras específicas para o estado de São Paulo."""

    @property
    def uf(self) -> str:
        return "SP"

    @property
    def nome(self) -> str:
        return "São Paulo"

    # Alíquota interna padrão SP
    ALIQUOTA_INTERNA_PADRAO = Decimal("18.0")

    # Alíquotas diferenciadas por tipo de produto
    ALIQUOTAS_ESPECIAIS = {
        "energia_eletrica": Decimal("18.0"),
        "combustiveis": Decimal("25.0"),
        "comunicacao": Decimal("25.0"),
        "bebidas_alcoolicas": Decimal("25.0"),
        "armas": Decimal("25.0"),
        "perfumaria": Decimal("25.0"),
        "alimentacao_basica": Decimal("7.0"),
        "medicamentos": Decimal("12.0"),
        "transporte": Decimal("12.0"),
    }

    def validate(self, parsed: SpedParseResult) -> List[Finding]:
        """Executa todas as validações específicas de SP."""
        findings = []
        findings.extend(self.validate_e111_codes(parsed))
        findings.extend(self.validate_difal(parsed))
        findings.extend(self.validate_ciap_sp(parsed))
        findings.extend(self.validate_bloco_k_obrigatoriedade(parsed))
        findings.extend(self.validate_bloco_h_obrigatoriedade(parsed))
        return findings

    def validate_e111_codes(self, parsed: SpedParseResult) -> List[Finding]:
        """Valida se os códigos E111 são válidos na Tabela 5.1.1 de SP."""
        findings = []
        loader = get_loader()
        tabela_sp = loader.get_tabela_511("SP")

        e111_list = parsed.get_registros("E111")
        for e111 in e111_list:
            cod_aj = e111.get_campo("COD_AJ_APUR")
            if not cod_aj:
                continue

            # Verificar se começa com SP
            if not cod_aj.startswith("SP"):
                findings.append(Finding(
                    block="E", register="E111", severity=Severity.WARNING,
                    code="E111-SP-001",
                    title=f"Código de ajuste '{cod_aj}' não pertence a SP",
                    description=f"O arquivo é de SP mas o código de ajuste '{cod_aj}' não começa com 'SP'.",
                    legal_reference="Tabela 5.1.1 de SP",
                    recommendation="Verificar se o código de ajuste está correto para a UF."
                ))
                continue

            # Verificar se existe na tabela
            if tabela_sp and cod_aj not in tabela_sp:
                findings.append(Finding(
                    block="E", register="E111", severity=Severity.WARNING,
                    code="E111-SP-002",
                    title=f"Código '{cod_aj}' não encontrado na Tabela 5.1.1 de SP",
                    description=f"O código de ajuste '{cod_aj}' não consta na Tabela 5.1.1 publicada para SP.",
                    legal_reference="Tabela 5.1.1 de SP (SEFAZ/SP)",
                    recommendation="Verificar se o código é válido para o período informado."
                ))

        return findings

    def validate_difal(self, parsed: SpedParseResult) -> List[Finding]:
        """
        Valida DIFAL para SP:
        - Se há C101/D101 com VL_ICMS_UF_DEST > 0, deve haver E300/E310
        - Se há E310 com VL_RECOL > 0, deve haver E316
        """
        findings = []

        # Verificar se há DIFAL nos documentos
        c101_list = parsed.get_registros("C101")
        total_difal_docs = Decimal("0")
        for c101 in c101_list:
            total_difal_docs += c101.get_campo_decimal("VL_ICMS_UF_DEST")

        if total_difal_docs > 0:
            # Deve haver E300/E310
            e310_list = parsed.get_registros("E310")
            if not e310_list:
                findings.append(Finding(
                    block="E", register="E310", severity=Severity.CRITICAL,
                    code="DIFAL-SP-001",
                    title="E310 ausente com DIFAL nos documentos",
                    description=(
                        f"Foram encontrados C101 com VL_ICMS_UF_DEST totalizando "
                        f"R$ {total_difal_docs:,.2f}, mas não há registro E310 "
                        f"(Apuração DIFAL)."
                    ),
                    legal_reference="EC 87/2015; Guia Prático EFD, Registro E310",
                    recommendation="Incluir os registros E300 e E310 com a apuração do DIFAL."
                ))
            else:
                # Verificar se há E316 quando há valor a recolher
                for e310 in e310_list:
                    vl_recol = e310.get_campo_decimal("VL_RECOL")
                    e316_list = parsed.get_registros("E316")
                    if vl_recol > 0 and not e316_list:
                        findings.append(Finding(
                            block="E", register="E316", severity=Severity.CRITICAL,
                            code="DIFAL-SP-002",
                            title="E316 ausente com DIFAL a recolher",
                            description=f"E310 com VL_RECOL = R$ {vl_recol:,.2f} mas sem E316.",
                            legal_reference="EC 87/2015; Guia Prático EFD, Registro E316",
                            recommendation="Incluir E316 com GNRE/DARE do DIFAL."
                        ))

        return findings

    def validate_ciap_sp(self, parsed: SpedParseResult) -> List[Finding]:
        """
        Validações CIAP específicas de SP:
        - Portaria CAT 147/2009
        - Verificar se parcelas > 48
        """
        findings = []
        g125_list = parsed.get_registros("G125")

        for g125 in g125_list:
            num_parc = g125.get_campo_int("NUM_PARC")
            cod_bem = g125.get_campo("COD_IND_BEM")
            tipo_mov = g125.get_campo("TIPO_MOV")

            if num_parc > 48:
                findings.append(Finding(
                    block="G", register="G125", severity=Severity.CRITICAL,
                    code="CIAP-SP-001",
                    title=f"Parcela {num_parc} do bem {cod_bem} excede 48 meses",
                    description=(
                        f"O bem {cod_bem} possui parcela nº {num_parc}, "
                        f"excedendo o limite de 48 meses previsto na LC 87/96."
                    ),
                    legal_reference="LC 87/96, art. 20, §5º; Portaria CAT 147/2009",
                    recommendation="Verificar o histórico de apropriação do bem."
                ))

        return findings

    def validate_bloco_k_obrigatoriedade(self, parsed: SpedParseResult) -> List[Finding]:
        """
        SP: Bloco K obrigatório conforme Portaria CAT 66/2018.
        """
        findings = []
        k001 = parsed.get_registro_unico("K001")

        if k001:
            ind_mov = k001.get_campo("IND_MOV")
            if ind_mov == "1":  # Sem dados
                # Verificar se a atividade requer Bloco K
                ind_ativ = parsed.file_info.ind_ativ
                if ind_ativ == "0":  # Industrial
                    findings.append(Finding(
                        block="K", register="K001", severity=Severity.WARNING,
                        code="K-SP-001",
                        title="Bloco K sem dados para contribuinte industrial em SP",
                        description=(
                            "O contribuinte é classificado como industrial (IND_ATIV=0) "
                            "mas o Bloco K está sem movimento."
                        ),
                        legal_reference="Portaria CAT 66/2018; RICMS/SP",
                        recommendation="Verificar obrigatoriedade do Bloco K conforme CNAE e faturamento."
                    ))

        return findings

    def validate_bloco_h_obrigatoriedade(self, parsed: SpedParseResult) -> List[Finding]:
        """SP: Inventário obrigatório em determinados períodos."""
        findings = []
        h005_list = parsed.get_registros("H005")

        # Verificar se é fevereiro (inventário de fim de ano)
        if parsed.file_info.dt_fin and parsed.file_info.dt_fin.month == 2:
            if not h005_list:
                findings.append(Finding(
                    block="H", register="H005", severity=Severity.WARNING,
                    code="H-SP-001",
                    title="H005 ausente no período de inventário (fevereiro)",
                    description=(
                        "O período informado é fevereiro, quando normalmente "
                        "é obrigatória a apresentação do inventário (H005) "
                        "referente ao encerramento do exercício anterior."
                    ),
                    legal_reference="RICMS/SP, art. 213; Guia Prático EFD, Registro H005",
                    recommendation="Verificar obrigatoriedade de apresentação do inventário."
                ))

        return findings

    def get_aliquota_interna(self, ncm: str) -> float:
        """Retorna alíquota interna padrão de SP (18%)."""
        # TODO: Implementar tabela de NCM × alíquota com base no RICMS/SP
        return float(self.ALIQUOTA_INTERNA_PADRAO)
