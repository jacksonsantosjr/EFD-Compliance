# -*- coding: utf-8 -*-
"""
Bloco 0 — Abertura, Identificação e Referências.
Mapeamento de campos dos registros conforme Guia Prático EFD v3.2.2.
"""

REGISTROS_BLOCO_0 = {
    "0000": {
        "REG": 0, "COD_VER": 1, "COD_FIN": 2, "DT_INI": 3, "DT_FIN": 4,
        "NOME": 5, "CNPJ": 6, "CPF": 7, "UF": 8, "IE": 9,
        "COD_MUN": 10, "IM": 11, "SUFRAMA": 12, "IND_PERFIL": 13, "IND_ATIV": 14,
    },
    "0001": {"REG": 0, "IND_MOV": 1},
    "0002": {"REG": 0, "CLAS_ESTAB_IND": 1},
    "0005": {
        "REG": 0, "FANTASIA": 1, "CEP": 2, "END": 3, "NUM": 4,
        "COMPL": 5, "BAIRRO": 6, "FONE": 7, "FAX": 8, "EMAIL": 9,
    },
    "0015": {"REG": 0, "UF_ST": 1, "IE_ST": 2},
    "0100": {
        "REG": 0, "NOME": 1, "CPF": 2, "CRC": 3, "CNPJ": 4,
        "CEP": 5, "END": 6, "NUM": 7, "COMPL": 8, "BAIRRO": 9,
        "FONE": 10, "FAX": 11, "EMAIL": 12, "COD_MUN": 13,
    },
    "0150": {
        "REG": 0, "COD_PART": 1, "NOME": 2, "COD_PAIS": 3, "CNPJ": 4,
        "CPF": 5, "IE": 6, "COD_MUN": 7, "SUFRAMA": 8, "END": 9,
        "NUM": 10, "COMPL": 11, "BAIRRO": 12,
    },
    "0175": {"REG": 0, "DT_ALT": 1, "NR_CAMPO": 2, "CONT_ANT": 3},
    "0190": {"REG": 0, "UNID": 1, "DESCR": 2},
    "0200": {
        "REG": 0, "COD_ITEM": 1, "DESCR_ITEM": 2, "COD_BARRA": 3,
        "COD_ANT_ITEM": 4, "UNID_INV": 5, "TIPO_ITEM": 6, "COD_NCM": 7,
        "EX_IPI": 8, "COD_GEN": 9, "COD_LST": 10, "ALIQ_ICMS": 11,
        "CEST": 12,
    },
    "0205": {
        "REG": 0, "DESCR_ANT_ITEM": 1, "DT_INI": 2, "DT_FIN": 3, "COD_ANT_ITEM": 4,
    },
    "0206": {"REG": 0, "COD_COMB": 1},
    "0210": {
        "REG": 0, "COD_ITEM_COMP": 1, "QTD_COMP": 2, "PERDA": 3,
    },
    "0220": {"REG": 0, "UNID_CONV": 1, "FAT_CONV": 2},
    "0300": {
        "REG": 0, "COD_IND_BEM": 1, "IDENT_MERC": 2, "DESCR_ITEM": 3,
        "COD_PRNC": 4, "COD_CTA": 5, "NR_PARC": 6,
    },
    "0305": {
        "REG": 0, "COD_CCUS": 1, "FUNC": 2, "VIDA_UTIL": 3,
    },
    "0400": {"REG": 0, "COD_NAT": 1, "DESCR_NAT": 2},
    "0450": {"REG": 0, "COD_INF": 1, "TXT": 2},
    "0460": {"REG": 0, "COD_OBS": 1, "TXT": 2},
    "0500": {
        "REG": 0, "DT_ALT": 1, "COD_NAT_CC": 2, "IND_CTA": 3,
        "NIVEL": 4, "COD_CTA": 5, "NOME_CTA": 6,
    },
    "0600": {"REG": 0, "DT_ALT": 1, "COD_CCUS": 2, "CCUS": 3},
    "0990": {"REG": 0, "QTD_LIN_0": 1},
}
