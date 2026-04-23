# -*- coding: utf-8 -*-
"""
Validador de Estoque — Bloco K (Produção/Estoque) e Bloco H (Inventário Físico).
Fase 3 do roadmap de evolução do EFD Compliance.

Aplica a equação de estoque e valida a coerência cruzada entre:
- K200 (Estoque escriturado)
- K230/K235 (Produção e consumo de insumos)
- K220 (Movimentações internas)
- H005/H010 (Inventário físico)
- K280 (Correções de estoque)
"""
from decimal import Decimal
from typing import List, Dict, Set, Optional
from collections import defaultdict

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult


class StockValidator:
    """Valida a consistência entre Bloco K (Produção/Estoque) e Bloco H (Inventário)."""

    def __init__(self, parsed: SpedParseResult):
        self.parsed = parsed
        self.findings: List[Finding] = []
        # Índice: COD_ITEM → descrição (0200)
        self.item_map: Dict[str, str] = {}
        self._build_item_index()

    def _build_item_index(self):
        """Constrói mapa de COD_ITEM → DESCR_ITEM a partir do registro 0200."""
        reg_0200 = self.parsed.get_registros("0200")
        for r in reg_0200:
            cod_item = r.get_campo("COD_ITEM")
            descr = r.get_campo("DESCR_ITEM")
            if cod_item:
                self.item_map[cod_item] = descr or "(sem descrição)"

    def _item_desc(self, cod_item: str) -> str:
        """Retorna descrição formatada de um item para uso em mensagens."""
        descr = self.item_map.get(cod_item, "")
        if descr:
            return f"{cod_item} ({descr})"
        return cod_item

    def validate_all(self) -> List[Finding]:
        """Executa todas as validações de estoque."""
        self.findings = []
        self._validate_k200_stock()
        self._validate_k230_k235_production()
        self._validate_k220_movements()
        self._validate_h_inventory()
        self._validate_k280_corrections()
        return self.findings

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 1: Equação de Estoque (K200)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_k200_stock(self):
        """Valida os registros K200 (estoque escriturado)."""
        k200_list = self.parsed.get_registros("K200")
        if not k200_list:
            return

        # Controle de duplicidade: (DT_EST, COD_ITEM, IND_EST) → contagem
        chaves_vistas: Dict[str, int] = defaultdict(int)
        itens_sem_cadastro: Set[str] = set()

        for k200 in k200_list:
            cod_item = k200.get_campo("COD_ITEM")
            qtd = k200.get_campo_decimal("QTD")
            dt_est = k200.get_campo("DT_EST")
            ind_est = k200.get_campo("IND_EST")

            if not cod_item:
                continue

            # STK-001: Estoque com quantidade negativa
            if qtd < Decimal("0"):
                self.findings.append(Finding(
                    block="K",
                    register="K200",
                    severity=Severity.CRITICAL,
                    code="STK-001",
                    title=f"Estoque negativo para item {self._item_desc(cod_item)}",
                    description=(
                        f"O registro K200 informa quantidade negativa ({qtd}) "
                        f"para o item {self._item_desc(cod_item)} na data {dt_est}.\n\n"
                        f"Tipo de estoque: {self._format_ind_est(ind_est)}"
                    ),
                    legal_reference="Guia Prático EFD ICMS/IPI, Registro K200",
                    recommendation="Corrija a quantidade em estoque. Valores negativos indicam erro de escrituração."
                ))

            # STK-002: Item sem cadastro no 0200
            if cod_item not in self.item_map and cod_item not in itens_sem_cadastro:
                itens_sem_cadastro.add(cod_item)
                self.findings.append(Finding(
                    block="K",
                    register="K200",
                    severity=Severity.CRITICAL,
                    code="STK-002",
                    title=f"Item {cod_item} no K200 ausente do cadastro 0200",
                    description=(
                        f"O item {cod_item} possui registro de estoque no K200 "
                        f"mas não está cadastrado no registro 0200 (Tabela de Identificação do Item).\n\n"
                        f"Data: {dt_est} | Quantidade: {qtd}"
                    ),
                    legal_reference="Guia Prático EFD, Registros 0200 e K200",
                    recommendation="Inclua o item no registro 0200 com NCM, unidade e descrição corretos."
                ))

            # STK-003: Verificar duplicidade de estoque (mesma data, item e tipo)
            chave = f"{dt_est}_{cod_item}_{ind_est}"
            chaves_vistas[chave] += 1

        # Gerar findings de duplicidade
        for chave, qtd_ocorrencias in chaves_vistas.items():
            if qtd_ocorrencias > 1:
                partes = chave.split("_")
                dt_est, cod_item, ind_est = partes[0], partes[1], partes[2] if len(partes) > 2 else ""
                self.findings.append(Finding(
                    block="K",
                    register="K200",
                    severity=Severity.WARNING,
                    code="STK-003",
                    title=f"Item {self._item_desc(cod_item)} duplicado no K200",
                    description=(
                        f"O item {self._item_desc(cod_item)} possui {qtd_ocorrencias} entradas "
                        f"no K200 para a mesma data ({dt_est}) e tipo de estoque "
                        f"({self._format_ind_est(ind_est)}).\n\n"
                        f"Cada combinação COD_ITEM × DT_EST × IND_EST deveria ser única."
                    ),
                    legal_reference="Guia Prático EFD, Registro K200",
                    recommendation="Consolide as entradas duplicadas em um único registro K200."
                ))

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 2: Produção e Consumo (K230/K235)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_k230_k235_production(self):
        """Valida ordens de produção (K230) e insumos consumidos (K235)."""
        k230_list = self.parsed.get_registros("K230")
        k235_list = self.parsed.get_registros("K235")

        if not k230_list:
            return

        # Construir mapa K235 → K230 pai (pela hierarquia de linhas)
        k235_por_k230: Dict[int, List] = defaultdict(list)
        k230_sorted = sorted(k230_list, key=lambda r: r.numero_linha)

        for k235 in k235_list:
            # Encontrar K230 pai (último K230 antes deste K235)
            pai = None
            for k230 in k230_sorted:
                if k230.numero_linha < k235.numero_linha:
                    pai = k230
                else:
                    break
            if pai:
                k235_por_k230[pai.numero_linha].append(k235)

        itens_sem_cadastro: Set[str] = set()

        for k230 in k230_list:
            cod_item = k230.get_campo("COD_ITEM")
            qtd_enc = k230.get_campo_decimal("QTD_ENC")
            dt_ini = k230.get_campo("DT_INI_OP")
            dt_fin = k230.get_campo("DT_FIN_OP")
            cod_doc = k230.get_campo("COD_DOC_OP")

            if not cod_item:
                continue

            doc_info = f"Ordem: {cod_doc}" if cod_doc else f"Período: {dt_ini} a {dt_fin}"

            # STK-004: K230 sem K235 (produção sem insumos)
            insumos = k235_por_k230.get(k230.numero_linha, [])
            if not insumos:
                self.findings.append(Finding(
                    block="K",
                    register="K230",
                    severity=Severity.CRITICAL,
                    code="STK-004",
                    title=f"Ordem de produção sem insumos — {self._item_desc(cod_item)}",
                    description=(
                        f"O registro K230 informa produção do item {self._item_desc(cod_item)} "
                        f"(Qtd encerrada: {qtd_enc}) mas não há registros K235 "
                        f"(insumos consumidos) associados.\n\n"
                        f"{doc_info}"
                    ),
                    legal_reference="Guia Prático EFD, Registros K230 e K235",
                    recommendation="Inclua os registros K235 com os insumos consumidos na produção."
                ))

            # STK-005: Insumos K235 sem cadastro no 0200
            for k235 in insumos:
                cod_insumo = k235.get_campo("COD_ITEM")
                if cod_insumo and cod_insumo not in self.item_map and cod_insumo not in itens_sem_cadastro:
                    itens_sem_cadastro.add(cod_insumo)
                    self.findings.append(Finding(
                        block="K",
                        register="K235",
                        severity=Severity.CRITICAL,
                        code="STK-005",
                        title=f"Insumo {cod_insumo} no K235 ausente do cadastro 0200",
                        description=(
                            f"O insumo {cod_insumo} consta no K235 como consumido na produção "
                            f"do item {self._item_desc(cod_item)}, mas não está cadastrado no 0200.\n\n"
                            f"{doc_info}"
                        ),
                        legal_reference="Guia Prático EFD, Registros 0200 e K235",
                        recommendation="Inclua o insumo no registro 0200."
                    ))

            # STK-006: Quantidade encerrada zerada
            if qtd_enc == Decimal("0"):
                self.findings.append(Finding(
                    block="K",
                    register="K230",
                    severity=Severity.WARNING,
                    code="STK-006",
                    title=f"Produção com quantidade zerada — {self._item_desc(cod_item)}",
                    description=(
                        f"O K230 informa QTD_ENC = 0 para o item {self._item_desc(cod_item)}.\n\n"
                        f"{doc_info}\n"
                        f"Produção com quantidade encerrada zerada pode indicar "
                        f"ordem em aberto ou erro de escrituração."
                    ),
                    legal_reference="Guia Prático EFD, Registro K230",
                    recommendation="Verifique se a ordem de produção foi efetivamente encerrada."
                ))

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 3: Movimentações Internas (K220)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_k220_movements(self):
        """Valida movimentações internas de estoque (K220)."""
        k220_list = self.parsed.get_registros("K220")
        if not k220_list:
            return

        itens_sem_cadastro: Set[str] = set()

        for k220 in k220_list:
            cod_item_ori = k220.get_campo("COD_ITEM_ORI")
            cod_item_dest = k220.get_campo("COD_ITEM_DEST")
            qtd = k220.get_campo_decimal("QTD")
            dt_mov = k220.get_campo("DT_MOV")

            # STK-007: Item origem igual ao destino
            if cod_item_ori and cod_item_dest and cod_item_ori == cod_item_dest:
                self.findings.append(Finding(
                    block="K",
                    register="K220",
                    severity=Severity.WARNING,
                    code="STK-007",
                    title=f"Movimentação circular — item {self._item_desc(cod_item_ori)}",
                    description=(
                        f"O K220 registra movimentação do item {self._item_desc(cod_item_ori)} "
                        f"onde a origem é igual ao destino (mesmo COD_ITEM).\n\n"
                        f"Data: {dt_mov} | Quantidade: {qtd}\n"
                        f"Movimentação de item para ele mesmo não faz sentido "
                        f"e pode indicar erro de escrituração."
                    ),
                    legal_reference="Guia Prático EFD, Registro K220",
                    recommendation="Revise os códigos de item de origem e destino da movimentação."
                ))

            # STK-008: Itens sem cadastro no 0200
            for cod_item, papel in [(cod_item_ori, "origem"), (cod_item_dest, "destino")]:
                if cod_item and cod_item not in self.item_map and cod_item not in itens_sem_cadastro:
                    itens_sem_cadastro.add(cod_item)
                    self.findings.append(Finding(
                        block="K",
                        register="K220",
                        severity=Severity.CRITICAL,
                        code="STK-008",
                        title=f"Item {cod_item} ({papel}) no K220 ausente do cadastro 0200",
                        description=(
                            f"O item {cod_item} consta como {papel} na movimentação K220 "
                            f"mas não está cadastrado no registro 0200.\n\n"
                            f"Data: {dt_mov} | Quantidade: {qtd}"
                        ),
                        legal_reference="Guia Prático EFD, Registros 0200 e K220",
                        recommendation="Inclua o item no registro 0200."
                    ))

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 4: Inventário Físico (H005/H010 × K200)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_h_inventory(self):
        """Valida inventário físico (H005/H010) e cruza com K200."""
        h005_list = self.parsed.get_registros("H005")
        h010_list = self.parsed.get_registros("H010")

        if not h005_list:
            return

        # Construir mapa H010 → H005 pai (hierarquia de linhas)
        h005_sorted = sorted(h005_list, key=lambda r: r.numero_linha)
        h010_por_h005: Dict[int, List] = defaultdict(list)

        for h010 in h010_list:
            pai = None
            for h005 in h005_sorted:
                if h005.numero_linha < h010.numero_linha:
                    pai = h005
                else:
                    break
            if pai:
                h010_por_h005[pai.numero_linha].append(h010)

        itens_sem_cadastro: Set[str] = set()
        itens_h010: Set[str] = set()  # Para cruzar com K200

        for h005 in h005_list:
            vl_inv_informado = h005.get_campo_decimal("VL_INV")
            dt_inv = h005.get_campo("DT_INV")
            mot_inv = h005.get_campo("MOT_INV")

            h010s_deste_h005 = h010_por_h005.get(h005.numero_linha, [])

            # STK-009: Somatório dos H010 diverge do VL_INV do H005
            if h010s_deste_h005:
                soma_h010 = sum(h.get_campo_decimal("VL_ITEM") for h in h010s_deste_h005)

                if vl_inv_informado > Decimal("0") and soma_h010 > Decimal("0"):
                    diferenca = abs(vl_inv_informado - soma_h010)
                    # Tolerância de R$ 0,02 por arredondamento
                    if diferenca > Decimal("0.02"):
                        self.findings.append(Finding(
                            block="H",
                            register="H005",
                            severity=Severity.CRITICAL,
                            code="STK-009",
                            title=f"Valor do inventário diverge da soma dos itens",
                            description=(
                                f"O H005 informa VL_INV = R$ {vl_inv_informado:,.2f}, "
                                f"mas a soma dos VL_ITEM dos H010 totaliza R$ {soma_h010:,.2f}.\n\n"
                                f"Diferença: R$ {diferenca:,.2f}\n"
                                f"Data do inventário: {dt_inv} | Motivo: {self._format_mot_inv(mot_inv)}"
                            ),
                            expected_value=f"R$ {vl_inv_informado:,.2f}",
                            actual_value=f"R$ {soma_h010:,.2f}",
                            legal_reference="Guia Prático EFD, Registros H005 e H010",
                            recommendation="Corrija os valores no H005 ou nos H010 para que sejam consistentes."
                        ))

            # Validar cada H010
            for h010 in h010s_deste_h005:
                cod_item = h010.get_campo("COD_ITEM")
                qtd = h010.get_campo_decimal("QTD")
                vl_unit = h010.get_campo_decimal("VL_UNIT")
                vl_item = h010.get_campo_decimal("VL_ITEM")

                if cod_item:
                    itens_h010.add(cod_item)

                # STK-010: Quantidade negativa no H010
                if qtd < Decimal("0"):
                    self.findings.append(Finding(
                        block="H",
                        register="H010",
                        severity=Severity.CRITICAL,
                        code="STK-010",
                        title=f"Quantidade negativa no inventário — {self._item_desc(cod_item)}",
                        description=(
                            f"O H010 informa quantidade {qtd} para o item "
                            f"{self._item_desc(cod_item)} no inventário de {dt_inv}."
                        ),
                        legal_reference="Guia Prático EFD, Registro H010",
                        recommendation="Corrija a quantidade. Valores negativos não são permitidos no inventário."
                    ))

                # STK-011: Item ausente no 0200
                if cod_item and cod_item not in self.item_map and cod_item not in itens_sem_cadastro:
                    itens_sem_cadastro.add(cod_item)
                    self.findings.append(Finding(
                        block="H",
                        register="H010",
                        severity=Severity.CRITICAL,
                        code="STK-011",
                        title=f"Item {cod_item} no H010 ausente do cadastro 0200",
                        description=(
                            f"O item {cod_item} consta no inventário físico (H010) "
                            f"mas não está cadastrado no registro 0200.\n\n"
                            f"Data do inventário: {dt_inv}"
                        ),
                        legal_reference="Guia Prático EFD, Registros 0200 e H010",
                        recommendation="Inclua o item no registro 0200."
                    ))

                # STK-013: Valor unitário zerado com quantidade > 0
                if qtd > Decimal("0") and vl_unit == Decimal("0"):
                    self.findings.append(Finding(
                        block="H",
                        register="H010",
                        severity=Severity.WARNING,
                        code="STK-013",
                        title=f"Item com valor unitário zerado — {self._item_desc(cod_item)}",
                        description=(
                            f"O item {self._item_desc(cod_item)} possui quantidade {qtd} "
                            f"no inventário mas VL_UNIT = R$ 0,00.\n\n"
                            f"Data do inventário: {dt_inv}\n"
                            f"Item com valor unitário zero pode indicar erro "
                            f"na avaliação do estoque."
                        ),
                        legal_reference="Guia Prático EFD, Registro H010; RICMS, art. 213",
                        recommendation="Verifique o critério de avaliação do estoque (custo médio, PEPS, etc.)."
                    ))

        # STK-012: Item com estoque no K200 mas ausente do inventário H010
        if itens_h010:
            k200_list = self.parsed.get_registros("K200")
            itens_k200_com_estoque: Set[str] = set()

            for k200 in k200_list:
                cod_item = k200.get_campo("COD_ITEM")
                qtd = k200.get_campo_decimal("QTD")
                ind_est = k200.get_campo("IND_EST")
                # Considerar apenas estoque próprio (IND_EST = 0)
                if cod_item and qtd > Decimal("0") and ind_est == "0":
                    itens_k200_com_estoque.add(cod_item)

            # Itens no K200 mas ausentes do H010
            itens_ausentes = itens_k200_com_estoque - itens_h010
            if itens_ausentes:
                # Limitar a 15 itens para não poluir
                itens_lista = sorted(itens_ausentes)
                if len(itens_lista) > 15:
                    itens_str = ", ".join(self._item_desc(i) for i in itens_lista[:15])
                    itens_str += f" e mais {len(itens_lista) - 15} itens"
                else:
                    itens_str = ", ".join(self._item_desc(i) for i in itens_lista)

                self.findings.append(Finding(
                    block="H",
                    register="H010",
                    severity=Severity.WARNING,
                    code="STK-012",
                    title=f"{len(itens_ausentes)} item(ns) com estoque no K200 ausente(s) do inventário H010",
                    description=(
                        f"Os seguintes itens possuem estoque próprio registrado no K200, "
                        f"mas não constam no inventário físico (H010):\n\n"
                        f"{itens_str}\n\n"
                        f"Todo item com saldo em estoque deveria constar no inventário."
                    ),
                    legal_reference="Guia Prático EFD, Registros K200 e H010; RICMS, art. 213",
                    recommendation="Inclua os itens faltantes no inventário físico (H010) ou ajuste o K200."
                ))

    # ═══════════════════════════════════════════════════════════════════════
    # GRUPO 5: Correções de Estoque (K280)
    # ═══════════════════════════════════════════════════════════════════════

    def _validate_k280_corrections(self):
        """Valida correções de estoque (K280)."""
        k280_list = self.parsed.get_registros("K280")
        if not k280_list:
            return

        itens_sem_cadastro: Set[str] = set()
        # Controle: item → {positiva, negativa}
        correcoes_por_item: Dict[str, dict] = defaultdict(lambda: {"pos": Decimal("0"), "neg": Decimal("0"), "dt": ""})

        for k280 in k280_list:
            cod_item = k280.get_campo("COD_ITEM")
            qtd_pos = k280.get_campo_decimal("QTD_COR_POS")
            qtd_neg = k280.get_campo_decimal("QTD_COR_NEG")
            dt_est = k280.get_campo("DT_EST")

            if not cod_item:
                continue

            # STK-014: Item sem cadastro no 0200
            if cod_item not in self.item_map and cod_item not in itens_sem_cadastro:
                itens_sem_cadastro.add(cod_item)
                self.findings.append(Finding(
                    block="K",
                    register="K280",
                    severity=Severity.CRITICAL,
                    code="STK-014",
                    title=f"Item {cod_item} no K280 ausente do cadastro 0200",
                    description=(
                        f"O item {cod_item} possui correção de estoque no K280 "
                        f"mas não está cadastrado no registro 0200.\n\n"
                        f"Data: {dt_est}"
                    ),
                    legal_reference="Guia Prático EFD, Registros 0200 e K280",
                    recommendation="Inclua o item no registro 0200."
                ))

            # Acumular correções por item
            correcoes_por_item[cod_item]["pos"] += qtd_pos
            correcoes_por_item[cod_item]["neg"] += qtd_neg
            if dt_est:
                correcoes_por_item[cod_item]["dt"] = dt_est

        # STK-015: Correção positiva e negativa simultânea para o mesmo item
        for cod_item, dados in correcoes_por_item.items():
            if dados["pos"] > Decimal("0") and dados["neg"] > Decimal("0"):
                self.findings.append(Finding(
                    block="K",
                    register="K280",
                    severity=Severity.WARNING,
                    code="STK-015",
                    title=f"Correção bidirecional no item {self._item_desc(cod_item)}",
                    description=(
                        f"O item {self._item_desc(cod_item)} possui correções no K280 "
                        f"tanto positivas ({dados['pos']}) quanto negativas ({dados['neg']}) "
                        f"no mesmo período.\n\n"
                        f"Última data: {dados['dt']}\n"
                        f"Correções simultâneas em ambas as direções podem indicar "
                        f"ajustes manuais para compensar erros de escrituração."
                    ),
                    legal_reference="Guia Prático EFD, Registro K280",
                    recommendation="Revise as correções e considere consolidar em um único ajuste líquido."
                ))

    # ═══════════════════════════════════════════════════════════════════════
    # Utilitários
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _format_ind_est(ind_est: str) -> str:
        """Formata o indicador de posse do estoque."""
        mapa = {
            "0": "Próprio — em posse do informante",
            "1": "De terceiros — em posse do informante",
            "2": "Próprio — em poder de terceiros",
        }
        return mapa.get(ind_est, f"Código {ind_est}")

    @staticmethod
    def _format_mot_inv(mot_inv: str) -> str:
        """Formata o motivo do inventário."""
        mapa = {
            "01": "Final do período",
            "02": "Mudança de forma de tributação",
            "03": "Baixa cadastral / Encerramento",
            "04": "Regime de pagamento — Condição do contribuinte",
            "05": "Determinação do fisco",
        }
        return mapa.get(mot_inv, f"Código {mot_inv}")
