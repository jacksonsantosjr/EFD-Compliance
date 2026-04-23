# -*- coding: utf-8 -*-
from parser.ecd_parser import EcdParseResult

class MathValidatorECD:
    def __init__(self, base_validator):
        self.base = base_validator
        self.parsed: EcdParseResult = base_validator.parsed
        
    def validate_lancamentos(self):
        """
        Valida se os lançamentos contábeis (I200) possuem as partidas dobradas balanceadas (I250).
        Total de Débitos = Total de Créditos.
        """
        lancamentos = self.parsed.get_registros("I200")
        partidas = self.parsed.get_registros("I250")
        
        if not lancamentos:
            return
            
        current_i200 = None
        total_debito = 0.0
        total_credito = 0.0
        
        # Pega todos I200 e I250 e ordena por numero_linha para ler sequencialmente
        todos = lancamentos + partidas
        todos.sort(key=lambda r: r.num_linha)
        
        for reg in todos:
            if reg.tipo == "I200":
                # Fechar o lançamento anterior e checar saldo
                if current_i200:
                    self._check_balance(current_i200, total_debito, total_credito)
                
                current_i200 = reg
                total_debito = 0.0
                total_credito = 0.0
                
            elif reg.tipo == "I250" and current_i200:
                # Layout ECD I250: |I250|COD_CTA|COD_CCUS|VL_DC|IND_DC|...
                try:
                    valor_str = reg.campos[4].replace(",", ".")
                    valor = float(valor_str)
                    ind_dc = reg.campos[5].upper()
                    
                    if ind_dc == "D":
                        total_debito += valor
                    elif ind_dc == "C":
                        total_credito += valor
                except (IndexError, ValueError):
                    pass
                    
        # Checar o último lançamento
        if current_i200:
            self._check_balance(current_i200, total_debito, total_credito)
            
    def _check_balance(self, i200_reg, debito, credito):
        d = round(debito, 2)
        c = round(credito, 2)
        if d != c:
            num_lanc = i200_reg.campos[2] if len(i200_reg.campos) > 2 else "N/A"
            dt_lanc = i200_reg.campos[3] if len(i200_reg.campos) > 3 else "N/A"
            self.base.add_issue(
                code="ECD-MATH-001",
                title="Lançamento Desbalanceado (Débito != Crédito)",
                description=f"Partidas dobradas não conferem. Débito: R$ {d:.2f} | Crédito: R$ {c:.2f}",
                level="error",
                category="Matemática",
                registro="I200",
                details=f"Lançamento '{num_lanc}' em {dt_lanc} (Linha {i200_reg.num_linha}). Diferença de R$ {abs(d-c):.2f}. Isso compromete o Balancete (J210)."
            )
