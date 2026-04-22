# -*- coding: utf-8 -*-
"""
Validador de Cruzamento entre Blocos.
Verifica a consistência dos dados entre os diferentes blocos do SPED EFD.
"""
from decimal import Decimal
from typing import List, Set

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult
from knowledge_base.loader import get_loader


class CrossBlockValidator:
    """Valida a consistência entre dados de blocos diferentes."""

    TOLERANCIA = Decimal("0.02")

    def __init__(self, parsed: SpedParseResult):
        self.parsed = parsed
        self.findings: List[Finding] = []
        self.loader = get_loader()

    def validate_all(self) -> List[Finding]:
        """Executa todas as validações de cruzamento."""
        self.findings = []
        self._validate_c190_x_e110()
        self._validate_c197_x_e110()
        self._validate_e111_x_e110()
        self._validate_g125_x_g110()
        self._validate_g140_x_0200()
        self._validate_e116_obrigatoriedade()
        self._validate_d190_x_e110()
        self._validate_h010_x_0200()
        return self.findings

    def _validate_c190_x_e110(self):
        """
        Cruza: Soma dos VL_ICMS do C190 (entradas) vs VL_TOT_CREDITOS do E110.
        Os C190 com CFOP de entrada (1xxx, 2xxx, 3xxx) devem somar o campo 06 do E110.
        """
        c190_list = self.parsed.get_registros("C190")
        e110 = self.parsed.get_registro_unico("E110")
        if not e110 or not c190_list:
            return

        soma_icms_entradas = Decimal("0")
        for c190 in c190_list:
            cfop = c190.get_campo("CFOP")
            if cfop and cfop[0] in ("1", "2", "3"):
                soma_icms_entradas += c190.get_campo_decimal("VL_ICMS")

        vl_tot_creditos = e110.get_campo_decimal("VL_TOT_CREDITOS")
        diff = abs(soma_icms_entradas - vl_tot_creditos)

        if diff > self.TOLERANCIA and soma_icms_entradas > 0:
            self.findings.append(Finding(
                block="C×E", register="C190×E110", severity=Severity.WARNING,
                code="CxE-CROSS-001",
                title="Soma C190 entradas diverge de VL_TOT_CREDITOS do E110",
                description=(
                    f"A soma do VL_ICMS dos registros C190 com CFOP de entrada "
                    f"(1xxx, 2xxx, 3xxx) é R$ {soma_icms_entradas:,.2f}, "
                    f"enquanto o VL_TOT_CREDITOS (campo 06) do E110 é R$ {vl_tot_creditos:,.2f}.\n"
                    f"Diferença: R$ {diff:,.2f}\n"
                    f"Nota: Os C190 de saída e os ajustes (C197, E111) podem justificar a diferença."
                ),
                expected_value=f"R$ {vl_tot_creditos:,.2f}",
                actual_value=f"R$ {soma_icms_entradas:,.2f}",
                legal_reference="Guia Prático EFD, Registros C190 e E110",
                recommendation="Verificar se há C197 ou E111 de crédito que expliquem a diferença."
            ))

    def _validate_c197_x_e110(self):
        """
        Cruza: Soma dos VL_ICMS do C197 por tipo de ajuste vs campos do E110.
        O 4º caractere do COD_AJ determina o campo do E110 alimentado.
        """
        c197_list = self.parsed.get_registros("C197")
        e110 = self.parsed.get_registro_unico("E110")
        if not e110 or not c197_list:
            return

        # Agrupar valores por campo do E110
        somas_por_campo = {}
        for c197 in c197_list:
            cod_aj = c197.get_campo("COD_AJ")
            campo = self.loader.get_campo_e110_for_code(cod_aj)
            if campo in ("NAO_APLICAVEL_E110", "DESCONHECIDO"):
                continue
            vl_icms = c197.get_campo_decimal("VL_ICMS")
            vl_outros = c197.get_campo_decimal("VL_OUTROS")
            valor = vl_icms if vl_icms else vl_outros
            somas_por_campo[campo] = somas_por_campo.get(campo, Decimal("0")) + valor

        # Verificar contra campos do E110
        mapa_campos = {
            "VL_AJ_DEBITOS": "VL_AJ_DEBITOS",
            "VL_AJ_CREDITOS": "VL_AJ_CREDITOS",
            "VL_ESTORNOS_CRED": "VL_ESTORNOS_CRED",
            "VL_ESTORNOS_DEB": "VL_ESTORNOS_DEB",
        }

        for campo_tipo, campo_e110 in mapa_campos.items():
            soma_c197 = somas_por_campo.get(campo_tipo, Decimal("0"))
            if soma_c197 > 0:
                valor_e110 = e110.get_campo_decimal(campo_e110)
                # C197 pode compor parcialmente o campo, apenas reportar INFO
                self.findings.append(Finding(
                    block="C×E", register="C197×E110", severity=Severity.INFO,
                    code=f"CxE-C197-{campo_tipo[:3]}",
                    title=f"C197 totaliza R$ {soma_c197:,.2f} para {campo_e110}",
                    description=(
                        f"A soma dos C197 com 4º caractere = ajuste de {campo_tipo} "
                        f"totaliza R$ {soma_c197:,.2f}. "
                        f"O campo {campo_e110} do E110 é R$ {valor_e110:,.2f}."
                    ),
                    legal_reference="Guia Prático EFD, Registros C197 e E110",
                ))

    def _validate_e111_x_e110(self):
        """
        Cruza: Soma dos E111 por tipo (4º caractere) vs campos do E110.
        """
        e111_list = self.parsed.get_registros("E111")
        e110 = self.parsed.get_registro_unico("E110")
        if not e110 or not e111_list:
            return

        somas = {}
        for e111 in e111_list:
            cod_aj = e111.get_campo("COD_AJ_APUR")
            campo = self.loader.get_campo_e110_for_code(cod_aj)
            if campo in ("NAO_APLICAVEL_E110", "DESCONHECIDO"):
                continue
            valor = e111.get_campo_decimal("VL_AJ_APUR")
            somas[campo] = somas.get(campo, Decimal("0")) + valor

        # Mapear para campos específicos do E110
        validacoes = {
            "VL_TOT_AJ_DEBITOS": ("VL_TOT_AJ_DEBITOS", "campo 04"),
            "VL_ESTORNOS_CRED": ("VL_ESTORNOS_CRED", "campo 05"),
            "VL_TOT_AJ_CREDITOS": ("VL_TOT_AJ_CREDITOS", "campo 08"),
            "VL_ESTORNOS_DEB": ("VL_ESTORNOS_DEB", "campo 09"),
            "VL_TOT_DED": ("VL_TOT_DED", "campo 12"),
            "DEB_ESP": ("DEB_ESP", "campo 15"),
        }

        # O 4º char dos E111 mapeia para os campos "TOT_AJ":
        # 0 → VL_TOT_AJ_DEBITOS (campo 04)
        # 1 → VL_ESTORNOS_CRED (campo 05)
        # 2 → VL_TOT_AJ_CREDITOS (campo 08)
        # 3 → VL_ESTORNOS_DEB (campo 09)
        # 4 → VL_TOT_DED (campo 12)
        # 5 → DEB_ESP (campo 15)
        mapa_4char = {
            "VL_AJ_DEBITOS": ("VL_TOT_AJ_DEBITOS", "campo 04"),
            "VL_ESTORNOS_CRED": ("VL_ESTORNOS_CRED", "campo 05"),
            "VL_AJ_CREDITOS": ("VL_TOT_AJ_CREDITOS", "campo 08"),
            "VL_ESTORNOS_DEB": ("VL_ESTORNOS_DEB", "campo 09"),
            "VL_TOT_DED": ("VL_TOT_DED", "campo 12"),
            "DEB_ESP": ("DEB_ESP", "campo 15"),
        }

        for tipo_aj, (campo_e110, desc_campo) in mapa_4char.items():
            soma_e111 = somas.get(tipo_aj, Decimal("0"))
            if soma_e111 > 0:
                valor_e110 = e110.get_campo_decimal(campo_e110)
                diff = abs(soma_e111 - valor_e110)
                if diff > self.TOLERANCIA:
                    self.findings.append(Finding(
                        block="E", register="E111×E110", severity=Severity.CRITICAL,
                        code=f"E111-CROSS-{campo_e110[:6]}",
                        title=f"E111 soma R$ {soma_e111:,.2f} ≠ E110 {desc_campo} R$ {valor_e110:,.2f}",
                        description=(
                            f"A soma dos E111 com ajuste tipo '{tipo_aj}' "
                            f"deveria corresponder ao {desc_campo} do E110."
                        ),
                        expected_value=f"R$ {valor_e110:,.2f}",
                        actual_value=f"R$ {soma_e111:,.2f}",
                        legal_reference="Guia Prático EFD, Registros E111 e E110",
                        recommendation="Verificar se todos os E111 estão com o código de ajuste correto."
                    ))

    def _validate_g125_x_g110(self):
        """
        Cruza: Soma VL_PARC_PASS de todos os G125 tipo SI = SOM_PARC do G110.
        """
        g110 = self.parsed.get_registro_unico("G110")
        g125_list = self.parsed.get_registros("G125")
        if not g110 or not g125_list:
            return

        soma_parc = Decimal("0")
        for g125 in g125_list:
            soma_parc += g125.get_campo_decimal("VL_PARC_PASS")

        som_parc_g110 = g110.get_campo_decimal("SOM_PARC")
        diff = abs(soma_parc - som_parc_g110)

        if diff > self.TOLERANCIA:
            self.findings.append(Finding(
                block="G", register="G125×G110", severity=Severity.CRITICAL,
                code="GxG-CROSS-001",
                title="Soma dos G125 diverge de SOM_PARC do G110",
                description=(
                    f"Soma VL_PARC_PASS de todos os G125: R$ {soma_parc:,.2f}\n"
                    f"SOM_PARC do G110 (campo 05): R$ {som_parc_g110:,.2f}"
                ),
                expected_value=f"R$ {som_parc_g110:,.2f}",
                actual_value=f"R$ {soma_parc:,.2f}",
                legal_reference="Guia Prático EFD, Registros G110 e G125",
                recommendation="Verificar os valores das parcelas dos bens no CIAP."
            ))

    def _validate_g140_x_0200(self):
        """
        Cruza: Itens referenciados no G140 devem existir no cadastro 0200.
        """
        g140_list = self.parsed.get_registros("G140")
        reg_0200 = self.parsed.get_registros("0200")
        if not g140_list:
            return

        itens_cadastrados: Set[str] = set()
        for r in reg_0200:
            cod_item = r.get_campo("COD_ITEM")
            if cod_item:
                itens_cadastrados.add(cod_item)

        for g140 in g140_list:
            cod_item = g140.get_campo("COD_ITEM")
            if cod_item and cod_item not in itens_cadastrados:
                self.findings.append(Finding(
                    block="G", register="G140×0200", severity=Severity.CRITICAL,
                    code="GxO-CROSS-001",
                    title=f"Item '{cod_item}' do G140 não cadastrado no 0200",
                    description=f"O item '{cod_item}' referenciado no G140 não existe no cadastro de itens (0200).",
                    legal_reference="Guia Prático EFD, Registros G140 e 0200",
                    recommendation="Incluir o item no registro 0200 ou corrigir o código no G140."
                ))

    def _validate_e116_obrigatoriedade(self):
        """
        Verifica se o E116 está presente quando há ICMS a recolher.
        """
        e110 = self.parsed.get_registro_unico("E110")
        e116_list = self.parsed.get_registros("E116")
        if not e110:
            return

        icms_recolher = e110.get_campo_decimal("VL_ICMS_RECOLHER")
        deb_esp = e110.get_campo_decimal("DEB_ESP")

        if (icms_recolher > 0 or deb_esp > 0) and not e116_list:
            self.findings.append(Finding(
                block="E", register="E116", severity=Severity.CRITICAL,
                code="E116-MISS-001",
                title="E116 ausente com ICMS a recolher",
                description=(
                    f"O E110 indica VL_ICMS_RECOLHER = R$ {icms_recolher:,.2f} e/ou "
                    f"DEB_ESP = R$ {deb_esp:,.2f}, porém não há registro E116 "
                    f"com as obrigações a recolher (DARE/GNRE)."
                ),
                legal_reference="Guia Prático EFD, Registro E116",
                recommendation=(
                    "Incluir o(s) registro(s) E116 correspondente(s) com código de receita, "
                    "data de vencimento e valor."
                )
            ))

    def _validate_d190_x_e110(self):
        """
        Cruza: Soma dos VL_ICMS do D190 (entradas) contribui para VL_TOT_CREDITOS do E110.
        """
        d190_list = self.parsed.get_registros("D190")
        if not d190_list:
            return

        soma_icms_entradas_d = Decimal("0")
        for d190 in d190_list:
            cfop = d190.get_campo("CFOP")
            if cfop and cfop[0] in ("1", "2", "3"):
                soma_icms_entradas_d += d190.get_campo_decimal("VL_ICMS")

        if soma_icms_entradas_d > 0:
            self.findings.append(Finding(
                block="D×E", register="D190×E110", severity=Severity.INFO,
                code="DxE-CROSS-001",
                title=f"D190 entradas totaliza R$ {soma_icms_entradas_d:,.2f} de ICMS",
                description=(
                    f"A soma do VL_ICMS dos registros D190 (CT-e) com CFOP de entrada "
                    f"totaliza R$ {soma_icms_entradas_d:,.2f}. "
                    f"Este valor deve estar refletido como crédito no E110."
                ),
                legal_reference="Guia Prático EFD, Registros D190 e E110",
            ))

    def _validate_h010_x_0200(self):
        """Cruza: Itens no H010 devem existir no 0200."""
        h010_list = self.parsed.get_registros("H010")
        reg_0200 = self.parsed.get_registros("0200")
        if not h010_list:
            return

        itens_cadastrados: Set[str] = set()
        for r in reg_0200:
            cod_item = r.get_campo("COD_ITEM")
            if cod_item:
                itens_cadastrados.add(cod_item)

        itens_faltantes = set()
        for h010 in h010_list:
            cod_item = h010.get_campo("COD_ITEM")
            if cod_item and cod_item not in itens_cadastrados:
                itens_faltantes.add(cod_item)

        if itens_faltantes:
            self.findings.append(Finding(
                block="H", register="H010×0200", severity=Severity.CRITICAL,
                code="HxO-CROSS-001",
                title=f"{len(itens_faltantes)} iten(s) do inventário sem cadastro no 0200",
                description=f"Itens: {', '.join(sorted(list(itens_faltantes)[:10]))}{'...' if len(itens_faltantes) > 10 else ''}",
                legal_reference="Guia Prático EFD, Registros H010 e 0200",
                recommendation="Incluir os itens faltantes no registro 0200."
            ))
