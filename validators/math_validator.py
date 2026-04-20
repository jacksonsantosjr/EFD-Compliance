# -*- coding: utf-8 -*-
"""
Validador Matemático — verifica consistência interna dos registros.
Aplica fórmulas do Guia Prático para E110, G110, E210, E520.
"""
from decimal import Decimal
from typing import List

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult


class MathValidator:
    """Valida a consistência matemática interna dos registros de apuração."""

    TOLERANCIA = Decimal("0.02")  # Tolerância de R$ 0,02 para arredondamento

    def __init__(self, parsed: SpedParseResult):
        self.parsed = parsed
        self.findings: List[Finding] = []

    def validate_all(self) -> List[Finding]:
        """Executa todas as validações matemáticas."""
        self.findings = []
        self._validate_e110()
        self._validate_g110()
        self._validate_g125_parcelas()
        self._validate_e210()
        self._validate_e520()
        self._validate_bloco_9()
        return self.findings

    def _validate_e110(self):
        """
        Valida a fórmula do E110 conforme Guia Prático v3.2.2:
        
        VL_SLD_APURADO (campo 11) = 
            VL_TOT_DEBITOS (02) + VL_AJ_DEBITOS (03) + VL_TOT_AJ_DEBITOS (04)
            + VL_ESTORNOS_CRED (05)
            - VL_TOT_CREDITOS (06) - VL_AJ_CREDITOS (07) - VL_TOT_AJ_CREDITOS (08)
            - VL_ESTORNOS_DEB (09)
            - VL_SLD_CREDOR_ANT (10)
        
        Se resultado > 0 → VL_SLD_APURADO = resultado; VL_SLD_CREDOR_TRANSPORTAR = 0
        Se resultado <= 0 → VL_SLD_APURADO = 0; VL_SLD_CREDOR_TRANSPORTAR = |resultado|
        
        VL_ICMS_RECOLHER (13) = VL_SLD_APURADO (11) - VL_TOT_DED (12) + DEB_ESP (15)
        """
        e110_list = self.parsed.get_registros("E110")
        if not e110_list:
            self.findings.append(Finding(
                block="E", register="E110", severity=Severity.CRITICAL,
                code="E110-MISS-001", title="Registro E110 ausente",
                description="O registro E110 (Apuração do ICMS — Operações Próprias) não foi encontrado.",
                legal_reference="Guia Prático EFD, Seção do Bloco E, Registro E110",
                recommendation="Verificar se o arquivo contém o bloco E completo."
            ))
            return

        for e110 in e110_list:
            # Extrair valores decimais
            debitos = e110.get_campo_decimal("VL_TOT_DEBITOS")
            aj_deb = e110.get_campo_decimal("VL_AJ_DEBITOS")
            tot_aj_deb = e110.get_campo_decimal("VL_TOT_AJ_DEBITOS")
            est_cred = e110.get_campo_decimal("VL_ESTORNOS_CRED")
            creditos = e110.get_campo_decimal("VL_TOT_CREDITOS")
            aj_cred = e110.get_campo_decimal("VL_AJ_CREDITOS")
            tot_aj_cred = e110.get_campo_decimal("VL_TOT_AJ_CREDITOS")
            est_deb = e110.get_campo_decimal("VL_ESTORNOS_DEB")
            sld_cred_ant = e110.get_campo_decimal("VL_SLD_CREDOR_ANT")
            sld_apurado = e110.get_campo_decimal("VL_SLD_APURADO")
            tot_ded = e110.get_campo_decimal("VL_TOT_DED")
            icms_recolher = e110.get_campo_decimal("VL_ICMS_RECOLHER")
            sld_cred_transp = e110.get_campo_decimal("VL_SLD_CREDOR_TRANSPORTAR")
            deb_esp = e110.get_campo_decimal("DEB_ESP")

            # Cálculo do saldo
            total_debitos = debitos + aj_deb + tot_aj_deb + est_cred
            total_creditos = creditos + aj_cred + tot_aj_cred + est_deb + sld_cred_ant
            saldo_calc = total_debitos - total_creditos

            if saldo_calc > 0:
                sld_apurado_esperado = saldo_calc
                sld_cred_transp_esperado = Decimal("0")
            else:
                sld_apurado_esperado = Decimal("0")
                sld_cred_transp_esperado = abs(saldo_calc)

            # Verificar VL_SLD_APURADO
            diff_sld = abs(sld_apurado - sld_apurado_esperado)
            if diff_sld > self.TOLERANCIA:
                self.findings.append(Finding(
                    block="E", register="E110", severity=Severity.CRITICAL,
                    code="E110-MATH-001", title="VL_SLD_APURADO divergente",
                    description=(
                        f"O campo VL_SLD_APURADO (campo 11) do E110 não confere com o cálculo.\n"
                        f"Fórmula: (Débitos + Aj.Deb + Tot.Aj.Deb + Est.Cred) - "
                        f"(Créditos + Aj.Cred + Tot.Aj.Cred + Est.Deb + Sld.Cred.Ant)\n"
                        f"Total débitos: R$ {total_debitos:,.2f}\n"
                        f"Total créditos: R$ {total_creditos:,.2f}\n"
                        f"Saldo calculado: R$ {saldo_calc:,.2f}"
                    ),
                    expected_value=f"R$ {sld_apurado_esperado:,.2f}",
                    actual_value=f"R$ {sld_apurado:,.2f}",
                    legal_reference="Guia Prático EFD v3.2.2, Registro E110, Campo 11",
                    recommendation="Verificar os valores dos campos 02 a 10 do E110."
                ))

            # Verificar VL_SLD_CREDOR_TRANSPORTAR
            diff_transp = abs(sld_cred_transp - sld_cred_transp_esperado)
            if diff_transp > self.TOLERANCIA:
                self.findings.append(Finding(
                    block="E", register="E110", severity=Severity.CRITICAL,
                    code="E110-MATH-002",
                    title="VL_SLD_CREDOR_TRANSPORTAR divergente",
                    description=f"O saldo credor a transportar não confere com o cálculo.",
                    expected_value=f"R$ {sld_cred_transp_esperado:,.2f}",
                    actual_value=f"R$ {sld_cred_transp:,.2f}",
                    legal_reference="Guia Prático EFD v3.2.2, Registro E110, Campo 14",
                    recommendation="Verificar se há inconsistência nos campos de débito/crédito."
                ))

            # Verificar VL_ICMS_RECOLHER
            icms_recolher_esperado = sld_apurado_esperado - tot_ded + deb_esp
            if icms_recolher_esperado < 0:
                icms_recolher_esperado = Decimal("0")
            diff_recolher = abs(icms_recolher - icms_recolher_esperado)
            if diff_recolher > self.TOLERANCIA:
                self.findings.append(Finding(
                    block="E", register="E110", severity=Severity.CRITICAL,
                    code="E110-MATH-003",
                    title="VL_ICMS_RECOLHER divergente",
                    description=(
                        f"VL_ICMS_RECOLHER (campo 13) = VL_SLD_APURADO - VL_TOT_DED + DEB_ESP\n"
                        f"= R$ {sld_apurado_esperado:,.2f} - R$ {tot_ded:,.2f} + R$ {deb_esp:,.2f}"
                    ),
                    expected_value=f"R$ {icms_recolher_esperado:,.2f}",
                    actual_value=f"R$ {icms_recolher:,.2f}",
                    legal_reference="Guia Prático EFD v3.2.2, Registro E110, Campo 13",
                    recommendation="Verificar campos 11, 12 e 15 do E110."
                ))

    def _validate_g110(self):
        """
        Valida o G110 (CIAP):
        - ICMS_APROP (campo 09) = SOM_PARC (campo 05) × IND_PER_SAI (campo 08)
        """
        g110_list = self.parsed.get_registros("G110")
        for g110 in g110_list:
            som_parc = g110.get_campo_decimal("SOM_PARC")
            ind_per_sai = g110.get_campo_decimal("IND_PER_SAI")
            icms_aprop = g110.get_campo_decimal("ICMS_APROP")

            esperado = (som_parc * ind_per_sai).quantize(Decimal("0.01"))
            diff = abs(icms_aprop - esperado)

            if diff > self.TOLERANCIA:
                self.findings.append(Finding(
                    block="G", register="G110", severity=Severity.CRITICAL,
                    code="G110-MATH-001", title="ICMS_APROP divergente no CIAP",
                    description=(
                        f"ICMS_APROP (campo 09) = SOM_PARC (campo 05) × IND_PER_SAI (campo 08)\n"
                        f"= R$ {som_parc:,.2f} × {ind_per_sai} = R$ {esperado:,.2f}"
                    ),
                    expected_value=f"R$ {esperado:,.2f}",
                    actual_value=f"R$ {icms_aprop:,.2f}",
                    legal_reference="Guia Prático EFD v3.2.2, Registro G110, Campo 09",
                    recommendation="Verificar o cálculo do índice de participação e soma das parcelas."
                ))

    def _validate_g125_parcelas(self):
        """
        Valida cada parcela G125:
        VL_PARC_PASS = (VL_IMOB_ICMS_OP + VL_IMOB_ICMS_ST + VL_IMOB_ICMS_FRT + VL_IMOB_ICMS_DIF) / 48
        """
        g125_list = self.parsed.get_registros("G125")
        for g125 in g125_list:
            tipo_mov = g125.get_campo("TIPO_MOV")
            if tipo_mov != "SI":
                continue  # Validar apenas parcelas de saldo inicial

            icms_op = g125.get_campo_decimal("VL_IMOB_ICMS_OP")
            icms_st = g125.get_campo_decimal("VL_IMOB_ICMS_ST")
            icms_frt = g125.get_campo_decimal("VL_IMOB_ICMS_FRT")
            icms_dif = g125.get_campo_decimal("VL_IMOB_ICMS_DIF")
            vl_parc = g125.get_campo_decimal("VL_PARC_PASS")
            num_parc = g125.get_campo_int("NUM_PARC")
            cod_bem = g125.get_campo("COD_IND_BEM")

            total_icms = icms_op + icms_st + icms_frt + icms_dif
            if total_icms > 0:
                esperado = (total_icms / Decimal("48")).quantize(Decimal("0.01"))
                diff = abs(vl_parc - esperado)
                if diff > self.TOLERANCIA:
                    self.findings.append(Finding(
                        block="G", register="G125", severity=Severity.WARNING,
                        code="G125-MATH-001",
                        title=f"Parcela {num_parc} do bem {cod_bem} divergente",
                        description=(
                            f"VL_PARC_PASS = (ICMS_OP + ICMS_ST + ICMS_FRT + ICMS_DIF) / 48\n"
                            f"= (R$ {icms_op} + R$ {icms_st} + R$ {icms_frt} + R$ {icms_dif}) / 48\n"
                            f"= R$ {total_icms} / 48 = R$ {esperado}"
                        ),
                        expected_value=f"R$ {esperado}",
                        actual_value=f"R$ {vl_parc}",
                        legal_reference="LC 87/96, art. 20, §5º; Guia Prático EFD, Registro G125",
                        recommendation="Verificar os valores de ICMS do bem no CIAP."
                    ))

    def _validate_e210(self):
        """Valida consistência do E210 (ICMS-ST)."""
        e210_list = self.parsed.get_registros("E210")
        for e210 in e210_list:
            sld_cred_ant = e210.get_campo_decimal("VL_SLD_CRED_ANT_ST")
            devol = e210.get_campo_decimal("VL_DEVOL_ST")
            ressarc = e210.get_campo_decimal("VL_RESSARC_ST")
            out_cred = e210.get_campo_decimal("VL_OUT_CRED_ST")
            aj_cred = e210.get_campo_decimal("VL_AJ_CREDITOS_ST")
            retencao = e210.get_campo_decimal("VL_RETENCAO_ST")
            out_deb = e210.get_campo_decimal("VL_OUT_DEB_ST")
            aj_deb = e210.get_campo_decimal("VL_AJ_DEBITOS_ST")

            total_cred = sld_cred_ant + devol + ressarc + out_cred + aj_cred
            total_deb = retencao + out_deb + aj_deb
            saldo = total_deb - total_cred

            sld_dev_ant = e210.get_campo_decimal("VL_SLD_DEV_ANT_ST")
            if saldo > 0:
                esperado = saldo
            else:
                esperado = Decimal("0")

            diff = abs(sld_dev_ant - esperado)
            if diff > self.TOLERANCIA:
                self.findings.append(Finding(
                    block="E", register="E210", severity=Severity.WARNING,
                    code="E210-MATH-001", title="Saldo devedor ICMS-ST divergente",
                    description=f"Total débitos ST: R$ {total_deb:,.2f}, Total créditos ST: R$ {total_cred:,.2f}",
                    expected_value=f"R$ {esperado:,.2f}",
                    actual_value=f"R$ {sld_dev_ant:,.2f}",
                    legal_reference="Guia Prático EFD, Registro E210",
                ))

    def _validate_e520(self):
        """Valida consistência do E520 (IPI)."""
        e520_list = self.parsed.get_registros("E520")
        for e520 in e520_list:
            sd_ant = e520.get_campo_decimal("VL_SD_ANT_IPI")
            deb = e520.get_campo_decimal("VL_DEB_IPI")
            cred = e520.get_campo_decimal("VL_CRED_IPI")
            od = e520.get_campo_decimal("VL_OD_IPI")
            oc = e520.get_campo_decimal("VL_OC_IPI")
            sc = e520.get_campo_decimal("VL_SC_IPI")
            sd = e520.get_campo_decimal("VL_SD_IPI")

            # Saldo = Deb + OD - Cred - OC - SD_ANT
            saldo_calc = deb + od - cred - oc - sd_ant
            if saldo_calc > 0:
                sd_esperado = saldo_calc
                sc_esperado = Decimal("0")
            else:
                sd_esperado = Decimal("0")
                sc_esperado = abs(saldo_calc)

            if abs(sd - sd_esperado) > self.TOLERANCIA:
                self.findings.append(Finding(
                    block="E", register="E520", severity=Severity.WARNING,
                    code="E520-MATH-001", title="Saldo devedor IPI divergente",
                    expected_value=f"R$ {sd_esperado:,.2f}",
                    actual_value=f"R$ {sd:,.2f}",
                    legal_reference="Guia Prático EFD, Registro E520",
                ))

    def _validate_bloco_9(self):
        """Valida contagem do Bloco 9 contra registros reais."""
        reg_9900 = self.parsed.get_registros("9900")
        for r9900 in reg_9900:
            reg_tipo = r9900.get_campo("REG_BLC")
            qtd_declarada = r9900.get_campo_int("QTD_REG_BLC")
            qtd_real = len(self.parsed.get_registros(reg_tipo))

            if qtd_real > 0 and qtd_declarada != qtd_real:
                self.findings.append(Finding(
                    block="9", register="9900", severity=Severity.WARNING,
                    code="9900-COUNT-001",
                    title=f"Contagem do registro {reg_tipo} divergente",
                    description=f"O Bloco 9 declara {qtd_declarada} registros {reg_tipo}, mas foram encontrados {qtd_real}.",
                    expected_value=str(qtd_real),
                    actual_value=str(qtd_declarada),
                    legal_reference="Guia Prático EFD, Registro 9900",
                    recommendation="Verificar integridade do arquivo."
                ))
