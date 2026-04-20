# -*- coding: utf-8 -*-
"""
Bloco H — Inventário Físico.
"""

REGISTROS_BLOCO_H = {
    "H001": {"REG": 0, "IND_MOV": 1},
    "H005": {
        "REG": 0,
        "DT_INV": 1,       # Data do inventário
        "VL_INV": 2,       # Valor total do inventário
        "MOT_INV": 3,      # Motivo: 01=final período, 02=mudança tributação, 03=baixa, 04=regime pgto, 05=det.fiscal
    },
    "H010": {
        "REG": 0,
        "COD_ITEM": 1,     # Código do item (ref 0200)
        "UNID": 2,
        "QTD": 3,
        "VL_UNIT": 4,
        "VL_ITEM": 5,
        "IND_PROP": 6,     # 0=Própria, 1=Terceiros, 2=Em poder de terceiros
        "COD_PART": 7,
        "TXT_COMPL": 8,
        "COD_CTA": 9,
        "VL_ITEM_IR": 10,
    },
    "H020": {
        "REG": 0,
        "CST_ICMS": 1,
        "BC_ICMS": 2,
        "VL_ICMS": 3,
    },
    "H030": {
        "REG": 0,
        "VL_ICMS_OP": 1,
        "VL_BC_ICMS_ST": 2,
        "VL_ICMS_ST": 3,
        "VL_FCP": 4,
    },
    "H990": {"REG": 0, "QTD_LIN_H": 1},
}
