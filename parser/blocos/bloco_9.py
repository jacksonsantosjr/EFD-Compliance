# -*- coding: utf-8 -*-
"""
Bloco 9 — Controle e Encerramento do Arquivo Digital.
"""

REGISTROS_BLOCO_9 = {
    "9001": {"REG": 0, "IND_MOV": 1},
    "9900": {
        "REG": 0,
        "REG_BLC": 1,     # Registro do bloco referenciado
        "QTD_REG_BLC": 2, # Quantidade de registros daquele tipo
    },
    "9990": {"REG": 0, "QTD_LIN_9": 1},
    "9999": {"REG": 0, "QTD_LIN": 1},
}
