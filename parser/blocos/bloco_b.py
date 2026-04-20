# -*- coding: utf-8 -*-
"""
Bloco B — Apuração do ISS (DES-IF).
"""

REGISTROS_BLOCO_B = {
    "B001": {"REG": 0, "IND_DAD": 1},
    "B020": {
        "REG": 0, "IND_OPER": 1, "IND_EMIT": 2, "COD_PART": 3,
        "COD_MOD": 4, "COD_SIT": 5, "SER": 6, "NUM_DOC": 7,
        "CHV_NFE": 8, "DT_DOC": 9, "COD_MUN_SERV": 10,
        "VL_CONT": 11, "VL_MAT_TERC": 12, "VL_SUB": 13,
        "VL_ISNT_ISS": 14, "VL_DED_BC": 15, "VL_BC_ISS": 16,
        "VL_BC_ISS_RT": 17, "VL_ISS_RT": 18, "VL_ISS": 19,
        "COD_INF_OBS": 20,
    },
    "B025": {"REG": 0, "VL_CONT_P": 1, "VL_BC_ISS_P": 2, "ALIQ_ISS": 3, "VL_ISS_P": 4, "VL_ISNT_ISS_P": 5, "COD_SERV": 6},
    "B030": {"REG": 0, "COD_MOD": 1, "SER": 2, "NUM_DOC_INI": 3, "NUM_DOC_FIN": 4, "DT_DOC": 5, "QTD_CANC": 6, "VL_CONT": 7, "VL_ISNT_ISS": 8, "VL_BC_ISS": 9, "VL_ISS": 10, "COD_INF_OBS": 11},
    "B035": {"REG": 0, "VL_CONT_P": 1, "VL_BC_ISS_P": 2, "ALIQ_ISS": 3, "VL_ISS_P": 4, "VL_ISNT_ISS_P": 5, "COD_SERV": 6},
    "B350": {"REG": 0, "COD_CTD": 1, "CTA_ISS": 2, "CTA_COSIF": 3, "QTD_OCOR": 4, "COD_SERV": 5, "VL_CONT": 6, "VL_BC_ISS": 7, "ALIQ_ISS": 8, "VL_ISS": 9},
    "B420": {"REG": 0, "VL_CONT": 1, "VL_BC_ISS": 2, "ALIQ_ISS": 3, "VL_ISNT_ISS": 4, "VL_ISS": 5, "COD_SERV": 6},
    "B440": {"REG": 0, "IND_OPER": 1, "COD_PART": 2, "VL_CONT_RT": 3, "VL_BC_ISS_RT": 4, "VL_ISS_RT": 5},
    "B460": {"REG": 0, "IND_DED": 1, "VL_DED": 2, "NUM_PROC": 3, "IND_PROC": 4},
    "B470": {
        "REG": 0, "VL_CONT": 1, "VL_MAT_TERC": 2, "VL_MAT_PROP": 3,
        "VL_SUB": 4, "VL_ISNT": 5, "VL_DED_BC": 6, "VL_BC_ISS": 7,
        "VL_BC_ISS_RT": 8, "VL_ISS": 9, "VL_ISS_RT": 10,
        "VL_DED": 11, "VL_ISS_REC": 12, "VL_ISS_ST": 13, "VL_ISS_REC_UNI": 14,
    },
    "B500": {"REG": 0, "VL_REC": 1, "QTD_PROF": 2, "VL_OR": 3},
    "B510": {"REG": 0, "IND_PROF": 1, "IND_ESC": 2, "IND_SIT": 3, "NM_PROF": 4, "CPF_PROF": 5, "COD_PART": 6},
    "B990": {"REG": 0, "QTD_LIN_B": 1},
}
