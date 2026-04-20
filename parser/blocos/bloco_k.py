# -*- coding: utf-8 -*-
"""
Bloco K — Controle da Produção e do Estoque.
"""

REGISTROS_BLOCO_K = {
    "K001": {"REG": 0, "IND_MOV": 1},
    "K100": {"REG": 0, "DT_INI": 1, "DT_FIN": 2},
    "K200": {
        "REG": 0,
        "DT_EST": 1,       # Data do estoque
        "COD_ITEM": 2,     # Código do item (ref 0200)
        "QTD": 3,          # Quantidade em estoque
        "IND_EST": 4,      # 0=Próprio, 1=Terceiros, 2=Em poder de terceiros
        "COD_PART": 5,
    },
    "K210": {"REG": 0, "DT_INI_OS": 1, "DT_FIN_OS": 2, "COD_DOC_OS": 3, "COD_ITEM_ORI": 4, "QTD_ORI": 5},
    "K215": {"REG": 0, "COD_ITEM_DES": 1, "QTD_DES": 2},
    "K220": {
        "REG": 0,
        "DT_MOV": 1,
        "COD_ITEM_ORI": 2,
        "COD_ITEM_DEST": 3,
        "QTD": 4,
        "QTD_DEST": 5,
    },
    "K230": {
        "REG": 0,
        "DT_INI_OP": 1,
        "DT_FIN_OP": 2,
        "COD_DOC_OP": 3,
        "COD_ITEM": 4,      # Item produzido
        "QTD_ENC": 5,       # Quantidade encerrada
    },
    "K235": {
        "REG": 0,
        "DT_SAIDA": 1,
        "COD_ITEM": 2,      # Insumo consumido
        "QTD": 3,
        "COD_INS_SUBST": 4,
    },
    "K250": {
        "REG": 0,
        "DT_PROD": 1,
        "COD_ITEM": 2,      # Item produzido por terceiros
        "QTD": 3,
    },
    "K255": {
        "REG": 0,
        "DT_CONS": 1,
        "COD_ITEM": 2,      # Insumo consumido por terceiros
        "QTD": 3,
        "COD_INS_SUBST": 4,
    },
    "K260": {"REG": 0, "COD_OP_OS": 1, "COD_ITEM": 2, "DT_SAIDA": 3, "QTD_SAIDA": 4, "DT_RET": 5, "QTD_RET": 6},
    "K265": {"REG": 0, "COD_ITEM": 1, "QTD_CONS": 2, "QTD_RET": 3},
    "K270": {"REG": 0, "DT_INI_AP": 1, "DT_FIN_AP": 2, "COD_OP_OS": 3, "COD_ITEM": 4, "QTD_COR_POS": 5, "QTD_COR_NEG": 6, "ORIGEM": 7},
    "K275": {"REG": 0, "COD_ITEM": 1, "QTD_COR_POS": 2, "QTD_COR_NEG": 3, "ORIGEM": 4},
    "K280": {
        "REG": 0,
        "DT_EST": 1,
        "COD_ITEM": 2,
        "QTD_COR_POS": 3,
        "QTD_COR_NEG": 4,
        "IND_EST": 5,
        "COD_PART": 6,
    },
    "K290": {"REG": 0, "DT_INI_OP": 1, "DT_FIN_OP": 2, "COD_DOC_OP": 3},
    "K291": {"REG": 0, "COD_ITEM": 1, "QTD": 2},
    "K292": {"REG": 0, "COD_ITEM": 1, "QTD": 2},
    "K300": {"REG": 0, "DT_PROD": 1},
    "K301": {"REG": 0, "COD_ITEM": 1, "QTD": 2},
    "K302": {"REG": 0, "COD_ITEM": 1, "QTD": 2},
    "K990": {"REG": 0, "QTD_LIN_K": 1},
}
