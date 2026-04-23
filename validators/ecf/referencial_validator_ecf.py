# -*- coding: utf-8 -*-
from parser.ecf_parser import EcfParseResult
from validators.ecf.base_validator_ecf import ECFValidator

class ReferencialValidatorECF:
    """Validador do Plano de Contas Referencial e Saldos (Blocos J e K) da ECF."""

    def __init__(self, base_validator: ECFValidator):
        self.base = base_validator
        self.parsed: EcfParseResult = base_validator.parsed

    def validate_all(self):
        self._validate_mapeamento_j050_j051()
        self._validate_saldos_k155()
        self._validate_saldos_k355()

    def _validate_mapeamento_j050_j051(self):
        """
        Verifica se todas as contas analíticas (J050) possuem mapeamento referencial (J051).
        Na ECF, contas analíticas (IND_CTA = 'A' ou 'S' em layouts antigos, mas em geral 'A' para analítica)
        com saldo no período devem ter correspondência com o plano de contas da RFB.
        O J051 é sempre "filho" do J050.
        Layout J050: |J050|DT_ALT|COD_NAT|IND_CTA|NIVEL|COD_CTA|COD_CTA_SUP|CTA|
        Layout J051: |J051|COD_CCUS|COD_CTA_REF|
        """
        # Na estrutura atual do parser (que é sequencial), podemos ler a lista de registros
        # e fazer o "parent-child" pela ordem de aparição ou criando um dicionário das contas.
        # Mas EcfParseResult agrupa por tipo de registro (J050 em uma lista, J051 em outra).
        # A regra geral é: todo registro J050 analítico deve ser seguido por um ou mais J051.
        # Uma abordagem robusta é iterar por todos os registros na ordem em que aparecem no arquivo.
        
        # Obter todos os J050 e J051 e ordenar por número de linha
        j050_regs = self.parsed.get_registros("J050")
        j051_regs = self.parsed.get_registros("J051")
        
        if not j050_regs:
            return

        todos = j050_regs + j051_regs
        todos.sort(key=lambda r: r.numero_linha)

        current_j050 = None
        has_j051 = False
        
        for reg in todos:
            if reg.reg == "J050":
                # Verifica o J050 anterior, se era analítico e se teve J051
                if current_j050:
                    ind_cta = current_j050.get_campo_int("IND_CTA") if current_j050.CAMPOS else current_j050.campos_raw[3] if len(current_j050.campos_raw) > 3 else ""
                    if ind_cta == "A" and not has_j051:
                        cod_cta = current_j050.campos_raw[5] if len(current_j050.campos_raw) > 5 else "N/A"
                        nome_cta = current_j050.campos_raw[7] if len(current_j050.campos_raw) > 7 else "N/A"
                        
                        self.base.add_issue(
                            code="ECF-REF-001",
                            title="Conta Analítica sem Mapeamento Referencial (J050/J051)",
                            description=f"A conta analítica {cod_cta} - {nome_cta} não possui mapeamento para o Plano de Contas Referencial da RFB.",
                            level="error",
                            category="Compliance",
                            registro="J050",
                            details=f"Linha {current_j050.numero_linha}. O registro J051 é obrigatório para contas analíticas de resultado e patrimoniais."
                        )
                        
                current_j050 = reg
                has_j051 = False
                
            elif reg.reg == "J051" and current_j050:
                has_j051 = True
                
        # Validar o último J050
        if current_j050:
            ind_cta = current_j050.get_campo_int("IND_CTA") if current_j050.CAMPOS else current_j050.campos_raw[3] if len(current_j050.campos_raw) > 3 else ""
            if ind_cta == "A" and not has_j051:
                cod_cta = current_j050.campos_raw[5] if len(current_j050.campos_raw) > 5 else "N/A"
                nome_cta = current_j050.campos_raw[7] if len(current_j050.campos_raw) > 7 else "N/A"
                self.base.add_issue(
                    code="ECF-REF-001",
                    title="Conta Analítica sem Mapeamento Referencial (J050/J051)",
                    description=f"A conta analítica {cod_cta} - {nome_cta} não possui mapeamento referencial.",
                    level="error",
                    category="Compliance",
                    registro="J050",
                    details=f"Linha {current_j050.numero_linha}."
                )

    def _validate_saldos_k155(self):
        """
        K155 - Detalhes dos Saldos Contábeis (Patrimoniais).
        Regra básica: Saldo Final = Saldo Inicial + Débitos - Créditos (ou Créditos - Débitos dependendo da natureza)
        Porém, simplificadamente as empresas de auditoria checam: |Saldo Final| == |Saldo Inicial + (Débito - Crédito)| (ajustando a natureza de fato).
        Layout: |K155|COD_CTA|COD_CCUS|VL_SLD_INI|IND_VL_SLD_INI|VL_DEB|VL_CRED|VL_SLD_FIN|IND_VL_SLD_FIN|
        """
        k155_regs = self.parsed.get_registros("K155")
        for reg in k155_regs:
            try:
                cod_cta = reg.campos_raw[1] if len(reg.campos_raw) > 1 else ""
                vl_sld_ini = float(reg.campos_raw[3].replace(",", ".")) if len(reg.campos_raw) > 3 and reg.campos_raw[3] else 0.0
                ind_ini = reg.campos_raw[4].upper() if len(reg.campos_raw) > 4 else "D"
                vl_deb = float(reg.campos_raw[5].replace(",", ".")) if len(reg.campos_raw) > 5 and reg.campos_raw[5] else 0.0
                vl_cred = float(reg.campos_raw[6].replace(",", ".")) if len(reg.campos_raw) > 6 and reg.campos_raw[6] else 0.0
                vl_sld_fin = float(reg.campos_raw[7].replace(",", ".")) if len(reg.campos_raw) > 7 and reg.campos_raw[7] else 0.0
                ind_fin = reg.campos_raw[8].upper() if len(reg.campos_raw) > 8 else "D"
                
                # Tratar Natureza. D (Positivo), C (Negativo) para facilitar a matemática.
                ini_calc = vl_sld_ini if ind_ini == "D" else -vl_sld_ini
                fin_calc = vl_sld_fin if ind_fin == "D" else -vl_sld_fin
                
                calc_esperado = ini_calc + vl_deb - vl_cred
                
                # Tolerância de centavos
                if abs(calc_esperado - fin_calc) > 0.05:
                    # Inverte para string formatada
                    esperado_abs = abs(calc_esperado)
                    esperado_ind = "D" if calc_esperado >= 0 else "C"
                    self.base.add_issue(
                        code="ECF-REF-002",
                        title="Equação Matemática Incorreta em Saldo Patrimonial (K155)",
                        description=f"Conta {cod_cta}: Saldo Final Declarado (R$ {vl_sld_fin:.2f}{ind_fin}) diverge do Calculado (R$ {esperado_abs:.2f}{esperado_ind}).",
                        level="error",
                        category="Matemática",
                        registro="K155",
                        details=f"Linha {reg.numero_linha}: Saldo Inicial ({vl_sld_ini}{ind_ini}) + Débito ({vl_deb}) - Crédito ({vl_cred})."
                    )
            except Exception:
                pass

    def _validate_saldos_k355(self):
        """
        K355 - Saldos Finais das Contas de Resultado Antes do Encerramento.
        Geralmente são contas de resultado, não há Saldo Inicial (é zero).
        Regra matemática: Saldo Final = Débito - Crédito (se D) ou Crédito - Débito (se C).
        Layout: |K355|COD_CTA|COD_CCUS|VL_SLD_FIN|IND_VL_SLD_FIN|
        No K355 a ECF só pede Saldo Final e Indicador (os débitos/créditos são muitas vezes detalhados por LALUR/LACS no bloco M, ou no L300).
        Mas existe uma validação geral se IND_VL_SLD_FIN é vazio e valor > 0.
        """
        k355_regs = self.parsed.get_registros("K355")
        for reg in k355_regs:
            try:
                cod_cta = reg.campos_raw[1] if len(reg.campos_raw) > 1 else ""
                vl_sld_fin = float(reg.campos_raw[3].replace(",", ".")) if len(reg.campos_raw) > 3 and reg.campos_raw[3] else 0.0
                ind_fin = reg.campos_raw[4].upper() if len(reg.campos_raw) > 4 else ""
                
                if vl_sld_fin > 0 and ind_fin not in ["D", "C"]:
                    self.base.add_issue(
                        code="ECF-REF-003",
                        title="Indicador de Saldo Ausente em Conta de Resultado (K355)",
                        description=f"Conta {cod_cta} possui Saldo Final > 0 (R$ {vl_sld_fin:.2f}) mas não informou se é Débito ou Crédito.",
                        level="warning",
                        category="Compliance",
                        registro="K355",
                        details=f"Linha {reg.numero_linha}. Isso pode impactar o mapeamento para o LALUR."
                    )
            except Exception:
                pass
