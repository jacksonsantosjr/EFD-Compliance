# -*- coding: utf-8 -*-
"""
Validador Semântico — CFOP × CST × NCM.
Detecta combinações fiscais inválidas ou suspeitas que o PVA não verifica.
"""
from decimal import Decimal
from typing import List, Dict, Set

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult
from knowledge_base.semantic_rules import REGRAS_CFOP_CST, REGRAS_CFOP_NCM, REGRAS_CST_VALORES


class SemanticValidator:
    """Valida a consistência semântica entre CFOP, CST e NCM nos documentos fiscais."""

    def __init__(self, parsed: SpedParseResult):
        self.parsed = parsed
        self.findings: List[Finding] = []
        # Índice: COD_ITEM → COD_NCM (construído a partir do 0200)
        self.item_ncm_map: Dict[str, str] = {}
        self._build_item_ncm_index()

    def _build_item_ncm_index(self):
        """Constrói o mapa de COD_ITEM → COD_NCM a partir do registro 0200."""
        reg_0200 = self.parsed.get_registros("0200")
        for r in reg_0200:
            cod_item = r.get_campo("COD_ITEM")
            cod_ncm = r.get_campo("COD_NCM")
            if cod_item:
                self.item_ncm_map[cod_item] = cod_ncm or ""

    def validate_all(self) -> List[Finding]:
        """Executa todas as validações semânticas."""
        self.findings = []
        self._validate_c190_cfop_cst()
        self._validate_c170_cfop_ncm()
        self._validate_c170_cst_valores()
        return self.findings

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 1: Regras CFOP × CST aplicadas no C190 (consolidado)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_c190_cfop_cst(self):
        """Aplica regras do Grupo 1 sobre os registros C190, identificando o C100 pai."""
        c100_list = self.parsed.get_registros("C100")
        c190_list = self.parsed.get_registros("C190")

        # Construir mapa: para cada C190, identificar o C100 pai pela ordem hierárquica
        # No SPED, C190 aparece sempre abaixo do seu C100 pai
        c190_to_c100 = self._build_c190_to_c100_map()

        for idx, c190 in enumerate(c190_list):
            cfop = c190.get_campo("CFOP")
            cst = c190.get_campo("CST_ICMS")
            vl_icms = c190.get_campo_decimal("VL_ICMS")
            vl_bc = c190.get_campo_decimal("VL_BC_ICMS")
            aliq = c190.get_campo_decimal("ALIQ_ICMS")
            vl_red_bc = c190.get_campo_decimal("VL_RED_BC")

            if not cfop or not cst:
                continue

            # Identificar documento pai
            c100_pai = c190_to_c100.get(c190.numero_linha)
            num_doc = c100_pai.get_campo("NUM_DOC") if c100_pai else "N/D"
            cod_part = c100_pai.get_campo("COD_PART") if c100_pai else ""
            chv_nfe = c100_pai.get_campo("CHV_NFE") if c100_pai else ""

            for regra in REGRAS_CFOP_CST:
                if self._match_cfop_cst_rule(regra, cfop, cst, vl_icms, vl_bc, aliq):
                    sev = Severity.CRITICAL if regra["severity"] == "critical" else Severity.WARNING
                    
                    # Montar descrição com identificação do documento
                    doc_info = f"Documento Fiscal Nº {num_doc}"
                    if chv_nfe:
                        doc_info += f" | Chave: {chv_nfe}"
                    if cod_part:
                        doc_info += f" | Participante: {cod_part}"
                    
                    self.findings.append(Finding(
                        block="C",
                        register="C190",
                        severity=sev,
                        code=regra["code"],
                        title=f"{regra['title']} (CFOP {cfop} / CST {cst})",
                        description=(
                            f"{regra['description']}\n\n"
                            f"{doc_info}\n"
                            f"Dados encontrados no C190: CFOP: {cfop} | CST: {cst} | "
                            f"VL_BC_ICMS: R$ {vl_bc:,.2f} | ALIQ: {aliq}% | VL_ICMS: R$ {vl_icms:,.2f}"
                        ),
                        legal_reference=regra.get("legal_ref", ""),
                        recommendation="Verifique a combinação CFOP × CST e corrija a escrituração do documento fiscal."
                    ))

    def _match_cfop_cst_rule(self, regra: dict, cfop: str, cst: str,
                              vl_icms: Decimal, vl_bc: Decimal, aliq: Decimal) -> bool:
        """Verifica se um registro C190 atende aos critérios da regra."""
        check = regra.get("check", "")

        # --- SEM-001: Saída tributada integral sem destaque ---
        if check == "saida_tributada_sem_icms":
            if not any(cfop.startswith(p) for p in regra.get("cfop_starts", [])):
                return False
            if not self._cst_matches(cst, regra):
                return False
            return vl_bc == 0 or aliq == 0

        # --- SEM-002: Entrada isenta com crédito ---
        if check == "entrada_isenta_com_credito":
            if not any(cfop.startswith(p) for p in regra.get("cfop_starts", [])):
                return False
            if not self._cst_matches(cst, regra):
                return False
            return vl_icms > 0

        # --- SEM-003: Revenda com ST indevida ---
        if check == "revenda_com_st_indevida":
            if cfop not in regra.get("cfop_exact", []):
                return False
            return any(cst.endswith(s) for s in regra.get("cst_endswith", []))

        # --- SEM-004: Venda ST sem CST de ST ---
        if check == "venda_st_sem_cst_st":
            if cfop not in regra.get("cfop_exact", []):
                return False
            return not any(cst.endswith(s) for s in regra.get("cst_not_endswith", []))

        # --- SEM-005: Bonificação com ICMS ---
        if check == "bonificacao_com_icms":
            if cfop not in regra.get("cfop_exact", []):
                return False
            if not self._cst_matches(cst, regra):
                return False
            return vl_icms > 0

        # --- SEM-006: CFOP genérico tributado ---
        if check == "cfop_generico_tributado":
            if not any(cfop.endswith(s) for s in regra.get("cfop_endswith", [])):
                return False
            return self._cst_matches(cst, regra)

        # --- SEM-007: Origem de importação ---
        if check == "origem_importacao_verificar":
            cst_startswith = regra.get("cst_startswith", [])
            if not any(cst.startswith(s) for s in cst_startswith):
                return False
            # Apenas sinalizar para revisão
            return True

        return False

    def _cst_matches(self, cst: str, regra: dict) -> bool:
        """Verifica se o CST está na lista da regra (suporta 2 e 3 dígitos)."""
        cst_values = regra.get("cst_values", [])
        if cst in cst_values:
            return True
        # Tentar com/sem o dígito de origem
        if len(cst) == 3 and cst[1:] in cst_values:
            return True
        if len(cst) == 2 and any(v.endswith(cst) for v in cst_values):
            return True
        return False

    def _build_c190_to_c100_map(self) -> Dict:
        """
        Constrói um mapa de numero_linha do C190 -> registro C100 pai.
        No SPED, a hierarquia é por ordem de linhas:
        cada C190 pertence ao C100 mais recente antes dele.
        """
        c100_list = self.parsed.get_registros("C100")
        c190_list = self.parsed.get_registros("C190")

        if not c100_list or not c190_list:
            return {}

        # Ordenar C100 por numero_linha para busca eficiente
        c100_sorted = sorted(c100_list, key=lambda r: r.numero_linha)
        result_map = {}

        for c190 in c190_list:
            # Encontrar o C100 pai: é o último C100 cuja linha vem antes do C190
            pai = None
            for c100 in c100_sorted:
                if c100.numero_linha < c190.numero_linha:
                    pai = c100
                else:
                    break
            if pai:
                result_map[c190.numero_linha] = pai

        return result_map

    def _build_c170_to_c100_map(self) -> Dict:
        """
        Constrói um mapa de numero_linha do C170 -> registro C100 pai.
        Mesma lógica hierárquica do C190.
        """
        c100_list = self.parsed.get_registros("C100")
        c170_list = self.parsed.get_registros("C170")

        if not c100_list or not c170_list:
            return {}

        c100_sorted = sorted(c100_list, key=lambda r: r.numero_linha)
        result_map = {}

        for c170 in c170_list:
            pai = None
            for c100 in c100_sorted:
                if c100.numero_linha < c170.numero_linha:
                    pai = c100
                else:
                    break
            if pai:
                result_map[c170.numero_linha] = pai

        return result_map

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 2: Regras CFOP × NCM aplicadas no C170 (item a item)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_c170_cfop_ncm(self):
        """Aplica regras do Grupo 2 sobre os registros C170."""
        c170_list = self.parsed.get_registros("C170")
        if not c170_list:
            return

        # Construir mapa C170 → C100 pai
        c170_to_c100 = self._build_c170_to_c100_map()

        # Controle para não duplicar alertas por regra+cfop+ncm
        alertas_emitidos: Set[str] = set()

        for c170 in c170_list:
            cfop = c170.get_campo("CFOP")
            cod_item = c170.get_campo("COD_ITEM")
            ncm = self.item_ncm_map.get(cod_item, "")

            if not cfop or not ncm:
                continue

            # Identificar documento pai
            c100_pai = c170_to_c100.get(c170.numero_linha)
            num_doc = c100_pai.get_campo("NUM_DOC") if c100_pai else "N/D"

            for regra in REGRAS_CFOP_NCM:
                chave = f"{regra['code']}_{cfop}_{ncm}"
                if chave in alertas_emitidos:
                    continue

                matched = False

                if regra.get("check") == "transferencia_ncm_servico":
                    if cfop in regra.get("cfop_exact", []):
                        if any(ncm.startswith(p) for p in regra.get("ncm_starts", [])):
                            matched = True

                elif regra.get("check") == "producao_ncm_generico":
                    if cfop in regra.get("cfop_exact", []):
                        if ncm in regra.get("ncm_exact", []):
                            matched = True

                if matched:
                    alertas_emitidos.add(chave)
                    sev = Severity.CRITICAL if regra["severity"] == "critical" else Severity.WARNING
                    self.findings.append(Finding(
                        block="C",
                        register="C170",
                        severity=sev,
                        code=regra["code"],
                        title=f"{regra['title']} (CFOP {cfop} / NCM {ncm})",
                        description=(
                            f"{regra['description']}\n\n"
                            f"Documento Fiscal Nº {num_doc}\n"
                            f"Item: {cod_item} | CFOP: {cfop} | NCM: {ncm}"
                        ),
                        legal_reference=regra.get("legal_ref", ""),
                        recommendation="Verifique o NCM cadastrado no registro 0200 e a natureza da operação."
                    ))

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 3: Regras CST × Valores aplicadas no C170 (item a item)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_c170_cst_valores(self):
        """Aplica regras do Grupo 3 sobre os registros C170 (valores por item)."""
        c170_list = self.parsed.get_registros("C170")
        if not c170_list:
            return

        # Construir mapa C170 → C100 pai
        c170_to_c100 = self._build_c170_to_c100_map()

        # Controle: consolidar por CST×CFOP para não gerar 500 findings do mesmo tipo
        alertas_consolidados: Dict[str, dict] = {}

        for c170 in c170_list:
            cst = c170.get_campo("CST_ICMS")
            cfop = c170.get_campo("CFOP")
            vl_bc = c170.get_campo_decimal("VL_BC_ICMS")
            aliq = c170.get_campo_decimal("ALIQ_ICMS")
            vl_icms = c170.get_campo_decimal("VL_ICMS")
            vl_item = c170.get_campo_decimal("VL_ITEM")

            if not cst:
                continue

            # Identificar documento pai
            c100_pai = c170_to_c100.get(c170.numero_linha)
            num_doc = c100_pai.get_campo("NUM_DOC") if c100_pai else "N/D"

            for regra in REGRAS_CST_VALORES:
                check = regra.get("check", "")
                cst_endswith = regra.get("cst_endswith", [])

                if not any(cst.endswith(s) for s in cst_endswith):
                    continue

                matched = False

                if check == "cst00_sem_bc":
                    matched = (vl_bc == 0 or aliq == 0) and vl_item > 0

                elif check == "cst20_sem_reducao":
                    # Verificar no C190 consolidado se VL_RED_BC = 0
                    # Aqui checamos se o item tem BC = 0 (o que indicaria redução total)
                    matched = vl_bc == 0 and vl_item > 0

                elif check == "isenta_com_icms":
                    matched = vl_icms > 0

                elif check == "diferimento_aliq_cheia":
                    matched = vl_icms > 0 and aliq >= Decimal("18")

                elif check == "cst60_com_icms_proprio":
                    matched = vl_icms > 0

                if matched:
                    chave = f"{regra['code']}_{cst}_{cfop}"
                    if chave not in alertas_consolidados:
                        alertas_consolidados[chave] = {
                            "regra": regra,
                            "cst": cst,
                            "cfop": cfop or "N/A",
                            "qtd_itens": 0,
                            "vl_icms_total": Decimal("0"),
                            "docs_envolvidos": set(),
                        }
                    alertas_consolidados[chave]["qtd_itens"] += 1
                    alertas_consolidados[chave]["vl_icms_total"] += vl_icms
                    alertas_consolidados[chave]["docs_envolvidos"].add(num_doc)

        # Gerar findings consolidados
        for chave, dados in alertas_consolidados.items():
            regra = dados["regra"]
            sev = Severity.CRITICAL if regra["severity"] == "critical" else Severity.WARNING
            
            # Listar documentos envolvidos (limitar a 10 para não poluir)
            docs = sorted(dados["docs_envolvidos"])
            if len(docs) > 10:
                docs_str = ", ".join(docs[:10]) + f" e mais {len(docs) - 10}"
            else:
                docs_str = ", ".join(docs) if docs else "N/D"
            
            self.findings.append(Finding(
                block="C",
                register="C170",
                severity=sev,
                code=regra["code"],
                title=f"{regra['title']} (CST {dados['cst']} / CFOP {dados['cfop']})",
                description=(
                    f"{regra['description']}\n\n"
                    f"Documentos Fiscais Nº: {docs_str}\n"
                    f"Encontrados {dados['qtd_itens']} item(ns) com esta inconsistência.\n"
                    f"Valor total de ICMS envolvido: R$ {dados['vl_icms_total']:,.2f}"
                ),
                legal_reference=regra.get("legal_ref", ""),
                recommendation="Revise a escrituração dos itens e corrija o CST ou os valores de ICMS."
            ))
