# -*- coding: utf-8 -*-
from parser.ecf_parser import EcfParseResult
from validators.ecf.base_validator_ecf import ECFValidator

class LalurValidatorECF:
    """Validador dos Livros LALUR e LACS (Blocos M e N) da ECF."""

    def __init__(self, base_validator: ECFValidator):
        self.base = base_validator
        self.parsed: EcfParseResult = base_validator.parsed

    def validate_all(self):
        self._validate_parte_b_m010()
        self._validate_parte_a_m300_m350()

    def _validate_parte_b_m010(self):
        """
        Valida a identificação e saldos iniciais da Parte B do LALUR/LACS (M010).
        Regras:
        - M010 sem data de criação é inválido se houver saldo.
        - M010 com tributo IRPJ e CSLL (identificador 'I' e 'C').
        Layout M010: |M010|COD_CTA_B|DESC_CTA_B|DT_CRIACAO|COD_TRIBUTO|VL_SLD_INI|IND_VL_SLD_INI|CNPJ_SIT_ESP|
        """
        m010_regs = self.parsed.get_registros("M010")
        for reg in m010_regs:
            try:
                cod_cta_b = reg.campos_raw[1] if len(reg.campos_raw) > 1 else ""
                dt_criacao = reg.campos_raw[3] if len(reg.campos_raw) > 3 else ""
                vl_sld_ini = float(reg.campos_raw[5].replace(",", ".")) if len(reg.campos_raw) > 5 and reg.campos_raw[5] else 0.0
                
                # Se há saldo inicial e não há data de criação, isso gera erro na RFB
                if vl_sld_ini > 0 and not dt_criacao:
                    self.base.add_issue(
                        code="ECF-LALUR-001",
                        title="Conta da Parte B sem Data de Criação (M010)",
                        description=f"A conta {cod_cta_b} possui Saldo Inicial (R$ {vl_sld_ini:.2f}) mas a Data de Criação não foi informada.",
                        level="error",
                        category="Compliance",
                        registro="M010",
                        details=f"Linha {reg.numero_linha}. Contas de controle de prejuízo fiscal/base negativa ou adições temporárias exigem data de formação."
                    )
            except Exception:
                pass

    def _validate_parte_a_m300_m350(self):
        """
        Valida as linhas de Adições e Exclusões da Parte A do e-Lalur (M300) e e-Lacs (M350).
        Regra:
        - Lançamentos com valor na Parte A (VL_LANCAMENTO > 0) devem possuir indicador de relação (IND_RELACAO) se exigido.
        Layout M300/M350: |M300|CODIGO|DESCRICAO|TIPO_LANCAMENTO|IND_RELACAO|VL_LANCAMENTO|HIST_LANCAMENTO|
        """
        for tipo_reg in ["M300", "M350"]:
            regs = self.parsed.get_registros(tipo_reg)
            for reg in regs:
                try:
                    codigo = reg.campos_raw[1] if len(reg.campos_raw) > 1 else ""
                    tipo_lanc = reg.campos_raw[3].upper() if len(reg.campos_raw) > 3 else "" # A=Adição, E=Exclusão, etc.
                    ind_relacao = reg.campos_raw[4] if len(reg.campos_raw) > 4 else ""
                    vl_lanc = float(reg.campos_raw[5].replace(",", ".")) if len(reg.campos_raw) > 5 and reg.campos_raw[5] else 0.0
                    
                    if vl_lanc > 0 and not ind_relacao:
                        # Adições ou exclusões geralmente precisam dizer se têm relação com a parte B ou com a contabilidade
                        self.base.add_issue(
                            code="ECF-LALUR-002",
                            title=f"Lançamento na Parte A sem Relação Declarada ({tipo_reg})",
                            description=f"O lançamento {codigo} possui valor de R$ {vl_lanc:.2f}, mas o Indicador de Relação (com contabilidade ou Parte B) está vazio.",
                            level="warning",
                            category="Compliance",
                            registro=tipo_reg,
                            details=f"Linha {reg.numero_linha}. Verifique se a adição/exclusão requer relacionamento na escrituração."
                        )
                    
                    if vl_lanc < 0:
                        self.base.add_issue(
                            code="ECF-LALUR-003",
                            title=f"Valor Negativo na Parte A ({tipo_reg})",
                            description=f"O lançamento {codigo} possui valor negativo (R$ {vl_lanc:.2f}). Valores no LALUR/LACS devem ser absolutos, a natureza de adição/exclusão é dada pelo código da linha.",
                            level="error",
                            category="Matemática",
                            registro=tipo_reg,
                            details=f"Linha {reg.numero_linha}."
                        )
                except Exception:
                    pass
