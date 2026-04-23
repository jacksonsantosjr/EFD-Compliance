# -*- coding: utf-8 -*-
from typing import List

class QualityValidatorECD:
    """Validador de Qualidade e Compliance Contábil da ECD."""
    
    def __init__(self, parent):
        self.parent = parent
        self.parsed = parent.parsed

    def validate_all(self):
        """Executa as auditorias de qualidade."""
        self._validate_saldos_invertidos()
        self._validate_zeramento_resultado()
        self._validate_cardinalidade_referencial()
        self._validate_historicos_vagos()

    def _validate_saldos_invertidos(self):
        """Regra ECD-QLTY-001: Contas do Ativo com saldo credor (Indício de Caixa Dois)."""
        i050_regs = self.parsed.get_registros("I050")
        i155_regs = self.parsed.get_registros("I155")
        
        # Mapeia natureza das contas
        natures = {}
        for r in i050_regs:
            cod = r.campos_raw[5] if len(r.campos_raw) > 5 else None
            nat = r.campos_raw[2] if len(r.campos_raw) > 2 else None
            if cod:
                natures[cod] = nat
                
        for r in i155_regs:
            cod = r.campos_raw[1] if len(r.campos_raw) > 1 else None
            vl_fin_str = r.campos_raw[7] if len(r.campos_raw) > 7 else "0"
            ind_fin = r.campos_raw[8].upper() if len(r.campos_raw) > 8 else "D"
            
            try:
                vl_fin = float(vl_fin_str.replace(",", "."))
            except:
                vl_fin = 0.0
                
            if cod and vl_fin > 0.05:
                nat = natures.get(cod)
                # Natureza 01 = Ativo. Saldo credor (C) em Ativo é anomalia.
                if nat == "01" and ind_fin == "C":
                    self.parent.add_issue(
                        code="ECD-QLTY-001",
                        title="Saldo Invertido no Ativo (Indício de Caixa Dois)",
                        description=f"A conta de Ativo '{cod}' possui saldo final CREDOR de R$ {vl_fin:.2f}. Ativos com saldo credor podem indicar omissão de receitas ou falta de contabilização de entradas.",
                        level="error",
                        category="Qualidade",
                        registro="I155"
                    )

    def _validate_zeramento_resultado(self):
        """Regra ECD-QLTY-002: Contas de Resultado com saldo final diferente de zero ao fim do exercício."""
        i050_regs = self.parsed.get_registros("I050")
        i155_regs = self.parsed.get_registros("I155")
        
        natures = {}
        for r in i050_regs:
            cod = r.campos_raw[5] if len(r.campos_raw) > 5 else None
            nat = r.campos_raw[2] if len(r.campos_raw) > 2 else None
            if cod:
                natures[cod] = nat
                
        for r in i155_regs:
            cod = r.campos_raw[1] if len(r.campos_raw) > 1 else None
            vl_fin_str = r.campos_raw[7] if len(r.campos_raw) > 7 else "0"
            
            try:
                vl_fin = float(vl_fin_str.replace(",", "."))
            except:
                vl_fin = 0.0
                
            if cod and vl_fin > 0.01: 
                nat = natures.get(cod)
                # Natureza 04 = Contas de Resultado. Devem ser zeradas no encerramento.
                if nat == "04":
                    self.parent.add_issue(
                        code="ECD-QLTY-002",
                        title="Ausência de Zeramento de Contas de Resultado",
                        description=f"A conta de resultado '{cod}' possui saldo final de R$ {vl_fin:.2f}. Todas as contas de receitas e despesas devem ser encerradas antes do balanço final.",
                        level="error",
                        category="Qualidade",
                        registro="I155"
                    )

    def _validate_cardinalidade_referencial(self):
        """Regra ECD-QLTY-003: Bloqueio de Cardinalidade Referencial (1 para N)."""
        i051_regs = self.parsed.get_registros("I051")
        
        # Mapeamento: conta_societaria -> lista de contas_referenciais
        mapeamento = {}
        for r in i051_regs:
            cod_soc = r.campos_raw[5] if len(r.campos_raw) > 5 else None
            cod_ref = r.campos_raw[2] if len(r.campos_raw) > 2 else None
            
            if cod_soc and cod_ref:
                if cod_soc not in mapeamento:
                    mapeamento[cod_soc] = set()
                mapeamento[cod_soc].add(cod_ref)
                
        for cod_soc, refs in mapeamento.items():
            if len(refs) > 1:
                refs_list = ", ".join(sorted(list(refs)))
                self.parent.add_issue(
                    code="ECD-QLTY-003",
                    title="Cardinalidade Inválida (Mapeamento 1 para N)",
                    description=f"A conta societária '{cod_soc}' está mapeada para múltiplas contas referenciais: [{refs_list}]. Isso causará erros na recuperação da ECF.",
                    level="error",
                    category="Compliance",
                    registro="I051"
                )

    def _validate_historicos_vagos(self):
        """Regra ECD-QLTY-004: Identificação de históricos genéricos/vagos (ITG 2000)."""
        import re
        i200_regs = self.parsed.get_registros("I200")
        
        # Termos suspeitos de serem genéricos demais
        termos_vagos = [
            r"\bDIVERSOS\b",
            r"\bLANCTO\b",
            r"\bLANCAMENTO\s+DO\s+MES\b",
            r"\bCONFORME\s+DOCUMENTO\b",
            r"\bVALOR\s+REFERENTE\s+AO\s+MES\b",
            r"\bPROVISAO\b" # Provisão sem detalhar o que é
        ]
        
        regex_pattern = "|".join(termos_vagos)
        
        for r in i200_regs:
            # I200: |I200|NUM_LCTO|DT_LCTO|VL_LCTO|IND_LCTO|
            # O histórico costuma vir no I250 associado ao I200 na ECD.
            pass
            
        # Na verdade, o histórico fica no I250 (Partida do Lançamento)
        i250_regs = self.parsed.get_registros("I250")
        
        for r in i250_regs:
            # I250: |I250|COD_CTA|COD_CCUS|VL_DC|IND_DC|NUM_ARQ|HIST|VL_ADC|
            historico = r.campos_raw[7] if len(r.campos_raw) > 7 else ""
            
            if historico:
                if re.search(regex_pattern, historico.upper()):
                    # Se o histórico for MUITO curto (ex: "DIVERSOS")
                    if len(historico.strip()) < 15:
                        self.parent.add_issue(
                            code="ECD-QLTY-004",
                            title="Histórico Contábil Genérico/Vago",
                            description=f"O lançamento na conta {r.campos_raw[1]} utiliza o histórico '{historico}'. Históricos vagos dificultam a identificação da essência econômica e são alvos de glosa pelo Fisco (ITG 2000).",
                            level="warning",
                            category="Compliance",
                            registro="I250"
                        )
