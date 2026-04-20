# -*- coding: utf-8 -*-
"""
Bloco G — Controle do Crédito de ICMS do Ativo Permanente (CIAP).
"""

REGISTROS_BLOCO_G = {
    "G001": {"REG": 0, "IND_MOV": 1},
    "G110": {
        "REG": 0,
        "DT_INI": 1,
        "DT_FIN": 2,
        "SALDO_IN_ICMS": 3,            # Campo 04 — Saldo inicial dos créditos de ICMS
        "SOM_PARC": 4,                  # Campo 05 — Soma das parcelas do período
        "VL_TRIB_EXP": 5,              # Campo 06 — Valor total de saídas tributadas e exportação
        "VL_TOTAL": 6,                  # Campo 07 — Valor total de saídas
        "IND_PER_SAI": 7,              # Campo 08 — Índice de participação (VL_TRIB_EXP / VL_TOTAL)
        "ICMS_APROP": 8,               # Campo 09 — SOM_PARC × IND_PER_SAI
        "SOM_ICMS_OC": 9,              # Campo 10 — Soma outras parcelas (G126)
    },
    "G125": {
        "REG": 0,
        "COD_IND_BEM": 1,     # Código do bem (ref 0300)
        "DT_MOV": 2,          # Data da movimentação
        "TIPO_MOV": 3,        # SI, IM, IA, CI, MC, BA, AT, PE
        "VL_IMOB_ICMS_OP": 4, # ICMS da operação própria
        "VL_IMOB_ICMS_ST": 5, # ICMS ST
        "VL_IMOB_ICMS_FRT": 6,# ICMS frete
        "VL_IMOB_ICMS_DIF": 7,# ICMS DIFAL
        "NUM_PARC": 8,        # Nº da parcela (1 a 48)
        "VL_PARC_PASS": 9,    # Valor da parcela = (OP+ST+FRT+DIF) / 48
    },
    "G126": {
        "REG": 0,
        "DT_INI": 1, "DT_FIN": 2,
        "NUM_PARC": 3,
        "VL_PARC_PASS": 4,
        "VL_TRIB_OC": 5,
        "VL_TOTAL_OC": 6,
        "IND_PER_SAI": 7,
        "VL_PARC_OC": 8,
    },
    "G130": {
        "REG": 0,
        "IND_EMIT": 1,
        "COD_PART": 2,
        "COD_MOD": 3,
        "SER": 4,
        "SUB": 5,
        "NUM_DOC": 6,
        "DT_DOC": 7,
        "CHV_NFE": 8,
    },
    "G140": {
        "REG": 0,
        "NUM_ITEM": 1,
        "COD_ITEM": 2,
        "QTDE": 3,
        "UNID": 4,
        "VL_ICMS_OP_ITEM": 5,
        "VL_BC_ICMS_ST_ITEM": 6,
        "VL_ICMS_ST_ITEM": 7,
        "VL_ICMS_FRT_ITEM": 8,
        "VL_ICMS_DIF_ITEM": 9,
    },
    "G990": {"REG": 0, "QTD_LIN_G": 1},
}
