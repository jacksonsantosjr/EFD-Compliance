# -*- coding: utf-8 -*-
"""
Detector de versão do layout SPED EFD.
Identifica a versão pelo campo COD_VER do registro 0000.
"""
from typing import Dict, Optional


# Mapeamento de COD_VER para versão legível
LAYOUT_VERSION_MAP: Dict[str, str] = {
    "001": "1.0.0",
    "002": "2.0.0",
    "003": "3.0.0",
    "004": "3.0.1",
    "005": "3.0.2",
    "006": "3.0.3",
    "007": "3.0.4",
    "008": "3.0.5",
    "009": "3.0.6",
    "010": "3.0.7",
    "011": "3.0.8",
    "012": "3.0.9",
    "013": "3.1.0",
    "014": "3.1.1",
    "015": "3.1.2",
    "016": "3.1.3",
    "017": "3.1.4",
    "018": "3.1.5",
    "019": "3.2.0",
    "020": "3.2.1",
    "021": "3.2.2",
}

# Agrupamento por família de versão (para selecionar o parser correto)
VERSION_FAMILY_MAP: Dict[str, str] = {
    "001": "v1",
    "002": "v2",
    "003": "v3_0", "004": "v3_0", "005": "v3_0", "006": "v3_0",
    "007": "v3_0", "008": "v3_0", "009": "v3_0", "010": "v3_0",
    "011": "v3_0", "012": "v3_0",
    "013": "v3_1", "014": "v3_1", "015": "v3_1", "016": "v3_1",
    "017": "v3_1", "018": "v3_1",
    "019": "v3_2", "020": "v3_2", "021": "v3_2",
}


def detect_layout_version(cod_ver: str) -> Optional[str]:
    """Retorna a versão legível do layout a partir do COD_VER."""
    return LAYOUT_VERSION_MAP.get(cod_ver)


def get_version_family(cod_ver: str) -> str:
    """Retorna a família de versão para selecionar o parser correto."""
    return VERSION_FAMILY_MAP.get(cod_ver, "v3_2")  # Default: mais recente
