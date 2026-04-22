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
        """Aplica regras do Grupo 1 sobre os registros C190."""
        c190_list = self.parsed.get_registros("C190")

        for c190 in c190_list:
            cfop = c190.get_campo("CFOP")
            cst = c190.get_campo("CST_ICMS")
            vl_icms = c190.get_campo_decimal("VL_ICMS")
            vl_bc = c190.get_campo_decimal("VL_BC_ICMS")
            aliq = c190.get_campo_decimal("ALIQ_ICMS")
            vl_red_bc = c190.get_campo_decimal("VL_RED_BC")

            if not cfop or not cst:
                continue

            for regra in REGRAS_CFOP_CST:
                if self._match_cfop_cst_rule(regra, cfop, cst, vl_icms, vl_bc, aliq):
                    sev = Severity.CRITICAL if regra["severity"] == "critical" else Severity.WARNING
                    self.findings.append(Finding(
                        block="C",
                        register="C190",
                        severity=sev,
                        code=regra["code"],
                        title=f"{regra['title']} (CFOP {cfop} / CST {cst})",
                        description=(
                            f"{regra['description']}\n\n"
                            f"Dados encontrados no C190:\n"
                            f"  CFOP: {cfop} | CST: {cst}\n"
                            f"  VL_BC_ICMS: R$ {vl_bc:,.2f} | ALIQ: {aliq}% | VL_ICMS: R$ {vl_icms:,.2f}"
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

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 2: Regras CFOP × NCM aplicadas no C170 (item a item)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_c170_cfop_ncm(self):
        """Aplica regras do Grupo 2 sobre os registros C170."""
        c170_list = self.parsed.get_registros("C170")
        if not c170_list:
            return

        # Controle para não duplicar alertas por regra+cfop+ncm
        alertas_emitidos: Set[str] = set()

        for c170 in c170_list:
            cfop = c170.get_campo("CFOP")
            cod_item = c170.get_campo("COD_ITEM")
            ncm = self.item_ncm_map.get(cod_item, "")

            if not cfop or not ncm:
                continue

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
                        }
                    alertas_consolidados[chave]["qtd_itens"] += 1
                    alertas_consolidados[chave]["vl_icms_total"] += vl_icms

        # Gerar findings consolidados
        for chave, dados in alertas_consolidados.items():
            regra = dados["regra"]
            sev = Severity.CRITICAL if regra["severity"] == "critical" else Severity.WARNING
            self.findings.append(Finding(
                block="C",
                register="C170",
                severity=sev,
                code=regra["code"],
                title=f"{regra['title']} (CST {dados['cst']} / CFOP {dados['cfop']})",
                description=(
                    f"{regra['description']}\n\n"
                    f"Encontrados {dados['qtd_itens']} item(ns) com esta inconsistência.\n"
                    f"Valor total de ICMS envolvido: R$ {dados['vl_icms_total']:,.2f}"
                ),
                legal_reference=regra.get("legal_ref", ""),
                recommendation="Revise a escrituração dos itens e corrija o CST ou os valores de ICMS."
            ))
