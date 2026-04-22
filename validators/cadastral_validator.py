# -*- coding: utf-8 -*-
"""
Validador Cadastral (Bloco 0150)
Executa a validação da situação cadastral dos fornecedores na Receita Federal
utilizando o serviço assíncrono de CNPJs em lote (Round-Robin)
"""
import asyncio
from typing import List, Dict, Set
from decimal import Decimal

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult
from validators.services.cnpj_service import CnpjService

class CadastralValidator:
    def __init__(self, parsed: SpedParseResult):
        self.parsed = parsed
        self.findings: List[Finding] = []
        self.bad_statuses = ["INAPTA", "BAIXADA", "SUSPENSA", "NULA"]

    async def validate_async(self) -> List[Finding]:
        """
        Executa a validação assíncrona de todos os participantes do bloco 0150
        """
        self.findings = []
        
        reg_0150 = self.parsed.get_bloco("0").get("0150", [])
        if not reg_0150:
            return self.findings

        # Extrair CNPJs únicos para consultar (ignorando exterior e CPFs)
        participantes_por_cnpj = {}
        for reg in reg_0150:
            cnpj_cpf = str(reg.get_campo("CNPJ_CPF")).strip()
            cod_part = str(reg.get_campo("COD_PART")).strip()
            
            # Filtro básico: Apenas CNPJs (14 digitos)
            if cnpj_cpf and len(cnpj_cpf) == 14:
                if cnpj_cpf not in participantes_por_cnpj:
                    participantes_por_cnpj[cnpj_cpf] = []
                participantes_por_cnpj[cnpj_cpf].append(reg)

        if not participantes_por_cnpj:
            return self.findings

        cnpjs_to_query = list(participantes_por_cnpj.keys())
        
        # Iniciar o serviço assíncrono
        service = CnpjService()
        
        try:
            # Controlar a concorrência para não exaurir sockets e causar rate limits imediatos
            semaphore = asyncio.Semaphore(5)
            
            async def bound_query(cnpj):
                async with semaphore:
                    return await service.query_cnpj(cnpj)
            
            # Executar todas as consultas em paralelo respeitando o semáforo
            tasks = [bound_query(cnpj) for cnpj in cnpjs_to_query]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analisar os resultados
            for result in results:
                if isinstance(result, Exception):
                    continue
                
                if result.get("status") == "success":
                    situacao = str(result.get("situacao", "")).strip().upper()
                    cnpj = result.get("cnpj", "")
                    clean_cnpj = service.clean_cnpj(cnpj)
                    
                    if situacao in self.bad_statuses:
                        # Achamos um CNPJ irregular! Vamos cruzar com C100
                        regs_0150 = participantes_por_cnpj.get(clean_cnpj, [])
                        for r_0150 in regs_0150:
                            cod_part = str(r_0150.get_campo("COD_PART")).strip()
                            nome = str(r_0150.get_campo("NOME")).strip()
                            self._generate_finding(clean_cnpj, situacao, cod_part, nome)

        finally:
            await service.close()
            
        return self.findings

    def _generate_finding(self, cnpj: str, situacao: str, cod_part: str, nome: str):
        """
        Gera um achado detalhado procurando as NFs de entrada desse fornecedor (C100/C190).
        """
        # Buscar C100 vinculados
        reg_c100 = self.parsed.get_bloco("C").get("C100", [])
        nfs_vinculadas = []
        valor_credito_risco = Decimal("0.00")
        
        for nfe in reg_c100:
            if nfe.get_campo("COD_PART") == cod_part and nfe.get_campo("IND_OPER") == "0":  # Operação de Entrada
                num_doc = nfe.get_campo("NUM_DOC")
                chv_nfe = nfe.get_campo("CHV_NFE")
                
                # Somar ICMS creditado nessa nota
                # Para ser mais preciso, buscamos os C190 filhos dessa nota
                filhos_c190 = nfe.children.get("C190", [])
                icms_nota = Decimal("0.00")
                if filhos_c190:
                    for c190 in filhos_c190:
                        icms = str(c190.get_campo("VL_ICMS") or "0")
                        if icms and icms != "None":
                            icms_nota += Decimal(icms.replace(",", "."))
                else:
                    # Se não tiver parseado os filhos, usa o cabeçalho
                    icms = str(nfe.get_campo("VL_ICMS") or "0")
                    if icms and icms != "None":
                        icms_nota += Decimal(icms.replace(",", "."))
                
                nfs_vinculadas.append(f"NF {num_doc} (R$ {icms_nota:.2f})")
                valor_credito_risco += icms_nota

        descricao = (
            f"O fornecedor {nome} (CNPJ: {cnpj}) está com a situação cadastral "
            f"na Receita Federal como '{situacao}'. A legislação veda a apropriação de "
            f"créditos de ICMS de documentos fiscais emitidos por empresas inidôneas ou irregulares."
        )

        if nfs_vinculadas:
            descricao += (
                f"\nForam encontradas {len(nfs_vinculadas)} nota(s) de entrada associadas "
                f"a este fornecedor (C100). "
                f"Valor de crédito de ICMS em risco: R$ {valor_credito_risco:.2f}."
                f"\nNotas: {', '.join(nfs_vinculadas[:5])}{'...' if len(nfs_vinculadas) > 5 else ''}"
            )
        else:
            descricao += "\nNão foram localizados registros C100 de entrada vinculados a este código de participante no período."

        self.findings.append(Finding(
            block="0",
            register="0150",
            severity=Severity.CRITICAL,
            code="CAD-001",
            title=f"Fornecedor Inapto/Baixado: Crédito Vedado (R$ {valor_credito_risco:.2f})",
            description=descricao,
            recommendation="Verifique a situação do fornecedor no SINTEGRA/RFB. O crédito destacado nas notas desse fornecedor deve ser estornado e as notas reclassificadas."
        ))
