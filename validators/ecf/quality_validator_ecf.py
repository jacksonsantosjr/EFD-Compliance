# -*- coding: utf-8 -*-
from typing import List

class QualityValidatorECF:
    """Validador de Qualidade e Compliance Tributário da ECF."""
    
    def __init__(self, parent):
        self.parent = parent
        self.parsed = parent.parsed

    def validate_all(self):
        """Executa as auditorias de qualidade."""
        self._validate_classificacao_deducoes()

    def _validate_classificacao_deducoes(self):
        """
        Regra ECF-QLTY-001: Identificação de impostos faturados em grupos de despesas operacionais.
        Impostos como ICMS, PIS, COFINS sobre vendas devem ser Deduções da Receita Bruta (3.01.01.03.xx).
        Se estiverem em Despesas Operacionais (3.01.01.07.xx), distorcem o Lucro Bruto.
        """
        j051_regs = self.parsed.get_registros("J051")
        
        # Mapeamento: COD_CTA (Societário) -> COD_CTA_REF (Referencial)
        mapeamento = {}
        for r in j051_regs:
            cod_soc = r.campos_raw[5] if len(r.campos_raw) > 5 else None
            cod_ref = r.campos_raw[2] if len(r.campos_raw) > 2 else ""
            if cod_soc:
                mapeamento[cod_soc] = cod_ref
                
        # Termos que indicam impostos sobre vendas no plano referencial
        # 3.01.01.03.xx -> Deduções da Receita Bruta
        # 3.01.01.07.xx -> Despesas Operacionais
        
        # Verificando K355 (Saldos de Resultado)
        k355_regs = self.parsed.get_registros("K355")
        for r in k355_regs:
            try:
                cod_soc = r.campos_raw[1] if len(r.campos_raw) > 1 else ""
                cod_ref = mapeamento.get(cod_soc, "")
                
                # Se a conta está no grupo de Despesas Operacionais (3.01.01.07)
                # Mas o código referencial ou a descrição sugere ser um imposto sobre venda
                # Exemplo: ICMS sobre Vendas (3.01.01.07.01.12 no plano antigo, mas deveria ser 3.01.01.03.01.xx)
                
                # Regra simplificada: Contas que deveriam ser 3.01.01.03 (Deduções) 
                # mas foram mapeadas em 3.01.01.07 (Despesas Operacionais).
                # Nota: Isso exige conhecimento do plano referencial exato, faremos uma busca por sufixos comuns de impostos.
                
                if cod_ref.startswith("3.01.01.07"):
                    # Verificação de códigos específicos que costumam ser mapeados errado
                    # ICMS s/ Vendas, PIS s/ Faturamento, etc.
                    pass # Implementação futura com dicionário completo de De-Para
            except:
                pass
        
        # Para esta versão inicial, vamos focar no alerta de "Indício de Erro de Classificação"
        # caso detectemos termos de impostos em contas de despesa.
        # Mas como não temos o nome da conta societária no K355 (só no J050),
        # vamos usar o J050.
        
        j050_regs = self.parsed.get_registros("J050")
        for r in j050_regs:
            try:
                nome_cta = r.campos_raw[7].upper() if len(r.campos_raw) > 7 else ""
                cod_soc = r.campos_raw[5] if len(r.campos_raw) > 5 else ""
                cod_ref = mapeamento.get(cod_soc, "")
                
                palavras_chave = ["ICMS SOBRE", "PIS SOBRE", "COFINS SOBRE", "ISS SOBRE"]
                if any(p in nome_cta for p in palavras_chave):
                    if cod_ref.startswith("3.01.01.07"):
                        self.parent.add_issue(
                            code="ECF-QLTY-001",
                            title="Erro Provável de Classificação (Dedução vs Despesa)",
                            description=f"A conta '{nome_cta}' (Ref: {cod_ref}) parece ser um imposto sobre venda, mas está mapeada como Despesa Operacional. O correto é 'Deduções da Receita Bruta' (3.01.01.03).",
                            level="warning",
                            category="Compliance",
                            registro="J051"
                        )
            except:
                pass
