# -*- coding: utf-8 -*-
"""
Bloco E — Apuração do ICMS e do IPI.
"""

REGISTROS_BLOCO_E = {
    "E001": {"REG": 0, "IND_MOV": 1},
    "E100": {"REG": 0, "DT_INI": 1, "DT_FIN": 2},
    "E110": {
        "REG": 0,
        "VL_TOT_DEBITOS": 1,       # Campo 02
        "VL_AJ_DEBITOS": 2,        # Campo 03
        "VL_TOT_AJ_DEBITOS": 3,    # Campo 04
        "VL_ESTORNOS_CRED": 4,     # Campo 05
        "VL_TOT_CREDITOS": 5,      # Campo 06
        "VL_AJ_CREDITOS": 6,       # Campo 07
        "VL_TOT_AJ_CREDITOS": 7,   # Campo 08
        "VL_ESTORNOS_DEB": 8,      # Campo 09
        "VL_SLD_CREDOR_ANT": 9,    # Campo 10
        "VL_SLD_APURADO": 10,      # Campo 11
        "VL_TOT_DED": 11,          # Campo 12
        "VL_ICMS_RECOLHER": 12,    # Campo 13
        "VL_SLD_CREDOR_TRANSPORTAR": 13,  # Campo 14
        "DEB_ESP": 14,             # Campo 15
    },
    "E111": {
        "REG": 0, "COD_AJ_APUR": 1, "DESCR_COMPL_AJ": 2, "VL_AJ_APUR": 3,
    },
    "E112": {
        "REG": 0, "NUM_DA": 1, "NUM_PROC": 2, "IND_PROC": 3,
        "PROC": 4, "TXT_COMPL": 5,
    },
    "E113": {
        "REG": 0, "COD_PART": 1, "COD_MOD": 2, "SER": 3,
        "SUB": 4, "NUM_DOC": 5, "DT_DOC": 6, "COD_ITEM": 7,
        "VL_AJ_ITEM": 8, "CHV_DOCe": 9,
    },
    "E115": {
        "REG": 0, "COD_INF_ADIC": 1, "VL_INF_ADIC": 2, "DESCR_COMPL_AJ": 3,
    },
    "E116": {
        "REG": 0, "COD_OR": 1, "VL_OR": 2, "DT_VCTO": 3,
        "COD_REC": 4, "NUM_PROC": 5, "IND_PROC": 6,
        "PROC": 7, "TXT_COMPL": 8, "MES_REF": 9,
    },
    # Sub-apuração ICMS-ST
    "E200": {"REG": 0, "UF": 1, "DT_INI": 2, "DT_FIN": 3},
    "E210": {
        "REG": 0,
        "IND_MOV_ST": 1,
        "VL_SLD_CRED_ANT_ST": 2,
        "VL_DEVOL_ST": 3,
        "VL_RESSARC_ST": 4,
        "VL_OUT_CRED_ST": 5,
        "VL_AJ_CREDITOS_ST": 6,
        "VL_RETENCAO_ST": 7,
        "VL_OUT_DEB_ST": 8,
        "VL_AJ_DEBITOS_ST": 9,
        "VL_SLD_DEV_ANT_ST": 10,
        "VL_DEDUCOES_ST": 11,
        "VL_ICMS_RECOL_ST": 12,
        "VL_SLD_CRED_ST_TRANSPORTAR": 13,
        "DEB_ESP_ST": 14,
    },
    "E220": {"REG": 0, "COD_AJ_APUR": 1, "DESCR_COMPL_AJ": 2, "VL_AJ_APUR": 3},
    "E230": {"REG": 0, "NUM_DA": 1, "NUM_PROC": 2, "IND_PROC": 3, "PROC": 4, "TXT_COMPL": 5},
    "E240": {"REG": 0, "COD_PART": 1, "COD_MOD": 2, "SER": 3, "SUB": 4, "NUM_DOC": 5, "DT_DOC": 6, "COD_ITEM": 7, "VL_AJ_ITEM": 8, "CHV_DOCe": 9},
    "E250": {
        "REG": 0, "COD_OR": 1, "VL_OR": 2, "DT_VCTO": 3,
        "COD_REC": 4, "NUM_PROC": 5, "IND_PROC": 6,
        "PROC": 7, "TXT_COMPL": 8, "MES_REF": 9,
    },
    # Sub-apuração DIFAL/FCP
    "E300": {"REG": 0, "UF": 1, "DT_INI": 2, "DT_FIN": 3},
    "E310": {
        "REG": 0,
        "IND_MOV_DIFAL": 1,
        "VL_SLD_CRED_ANT_DIFAL": 2,
        "VL_TOT_DEBITOS_DIFAL": 3,
        "VL_OUT_DEB_DIFAL": 4,
        "VL_TOT_DEB_FCP": 5,
        "VL_TOT_CREDITOS_DIFAL": 6,
        "VL_TOT_CRED_FCP": 7,
        "VL_OUT_CRED_DIFAL": 8,
        "VL_SLD_DEV_ANT_DIFAL": 9,
        "VL_DEDUCOES_DIFAL": 10,
        "VL_RECOL": 11,
        "VL_SLD_CRED_TRANSPORTAR": 12,
        "DEB_ESP_DIFAL": 13,
    },
    "E311": {"REG": 0, "COD_AJ_APUR": 1, "DESCR_COMPL_AJ": 2, "VL_AJ_APUR": 3},
    "E312": {"REG": 0, "NUM_DA": 1, "NUM_PROC": 2, "IND_PROC": 3, "PROC": 4, "TXT_COMPL": 5},
    "E313": {"REG": 0, "COD_PART": 1, "COD_MOD": 2, "SER": 3, "SUB": 4, "NUM_DOC": 5, "DT_DOC": 6, "COD_ITEM": 7, "VL_AJ_ITEM": 8, "CHV_DOCe": 9},
    "E316": {
        "REG": 0, "COD_OR": 1, "VL_OR": 2, "DT_VCTO": 3,
        "COD_REC": 4, "NUM_PROC": 5, "IND_PROC": 6,
        "PROC": 7, "TXT_COMPL": 8, "MES_REF": 9,
    },
    # Apuração IPI
    "E500": {"REG": 0, "IND_APUR": 1, "DT_INI": 2, "DT_FIN": 3},
    "E510": {"REG": 0, "CFOP": 1, "CST_IPI": 2, "VL_CONT_IPI": 3, "VL_BC_IPI": 4, "VL_IPI": 5},
    "E520": {
        "REG": 0,
        "VL_SD_ANT_IPI": 1,
        "VL_DEB_IPI": 2,
        "VL_CRED_IPI": 3,
        "VL_OD_IPI": 4,
        "VL_OC_IPI": 5,
        "VL_SC_IPI": 6,
        "VL_SD_IPI": 7,
    },
    "E530": {"REG": 0, "IND_AJ": 1, "VL_AJ": 2, "COD_AJ": 3, "IND_DOC": 4, "NUM_DOC": 5, "DESCR_AJ": 6},
    "E531": {"REG": 0, "COD_PART": 1, "COD_MOD": 2, "SER": 3, "SUB": 4, "NUM_DOC": 5, "DT_DOC": 6, "COD_ITEM": 7, "VL_AJ_ITEM": 8, "CHV_NFE": 9},
    "E990": {"REG": 0, "QTD_LIN_E": 1},
}
