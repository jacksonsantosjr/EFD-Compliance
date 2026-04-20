# -*- coding: utf-8 -*-
"""
Parser principal do SPED EFD ICMS/IPI.
Lê o arquivo TXT line-by-line e organiza os registros por bloco.
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import date

from parser.registro import Registro
from parser.layout_detector import detect_layout_version, get_version_family
from parser.blocos.bloco_0 import REGISTROS_BLOCO_0
from parser.blocos.bloco_b import REGISTROS_BLOCO_B
from parser.blocos.bloco_c import REGISTROS_BLOCO_C
from parser.blocos.bloco_d import REGISTROS_BLOCO_D
from parser.blocos.bloco_e import REGISTROS_BLOCO_E
from parser.blocos.bloco_g import REGISTROS_BLOCO_G
from parser.blocos.bloco_h import REGISTROS_BLOCO_H
from parser.blocos.bloco_k import REGISTROS_BLOCO_K
from parser.blocos.bloco_1 import REGISTROS_BLOCO_1
from parser.blocos.bloco_9 import REGISTROS_BLOCO_9


# Mapeamento de prefixo de registro para bloco
BLOCO_MAP = {
    "0": "0",
    "B": "B",
    "C": "C",
    "D": "D",
    "E": "E",
    "G": "G",
    "H": "H",
    "K": "K",
    "1": "1",
    "9": "9",
}

# Mapeamento de registro para classe de campos
REGISTRO_CLASSES: Dict[str, Dict[str, int]] = {}
REGISTRO_CLASSES.update(REGISTROS_BLOCO_0)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_B)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_C)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_D)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_E)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_G)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_H)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_K)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_1)
REGISTRO_CLASSES.update(REGISTROS_BLOCO_9)


class SpedFileInfo:
    """Informações extraídas do registro 0000."""

    def __init__(self):
        self.cod_ver: str = ""
        self.layout_version: str = ""
        self.version_family: str = ""
        self.cod_fin: str = ""  # 0=Remessa original, 1=Retificadora
        self.dt_ini: Optional[date] = None
        self.dt_fin: Optional[date] = None
        self.nome: str = ""
        self.cnpj: str = ""
        self.cpf: str = ""
        self.uf: str = ""
        self.ie: str = ""
        self.cod_mun: str = ""
        self.im: str = ""
        self.suframa: str = ""
        self.ind_perfil: str = ""  # A, B ou C
        self.ind_ativ: str = ""  # 0=Industrial/Equiparado, 1=Outros
        self.total_linhas: int = 0


class SpedParseResult:
    """Resultado do parsing de um arquivo SPED EFD."""

    def __init__(self):
        self.file_info = SpedFileInfo()
        self.file_hash: str = ""
        self.filename: str = ""
        self.registros: Dict[str, List[Registro]] = {}
        self.blocos: Dict[str, Dict[str, List[Registro]]] = {}
        self.contagem_registros: Dict[str, int] = {}
        self.erros_parse: List[str] = []
        self.encoding_used: str = ""

    def get_registros(self, tipo: str) -> List[Registro]:
        """Retorna lista de registros de um tipo específico (ex: 'C190', 'E110')."""
        return self.registros.get(tipo, [])

    def get_registro_unico(self, tipo: str) -> Optional[Registro]:
        """Retorna o primeiro registro de um tipo (para registros que aparecem uma vez)."""
        regs = self.registros.get(tipo, [])
        return regs[0] if regs else None

    def get_bloco(self, bloco: str) -> Dict[str, List[Registro]]:
        """Retorna todos os registros de um bloco."""
        return self.blocos.get(bloco, {})

    @property
    def total_registros(self) -> int:
        return sum(len(regs) for regs in self.registros.values())


def _detect_encoding(file_path: Path) -> str:
    """Detecta o encoding do arquivo tentando latin-1, utf-8, cp1252."""
    encodings = ["latin-1", "utf-8", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                # Ler primeiras 100 linhas para validar
                for i, line in enumerate(f):
                    if i > 100:
                        break
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "latin-1"  # Fallback padrão do PVA


def _identify_bloco(reg: str) -> str:
    """Identifica o bloco de um registro pelo seu prefixo."""
    if not reg:
        return "?"
    primeiro_char = reg[0]
    return BLOCO_MAP.get(primeiro_char, "?")


def parse_sped_file(file_path: Path) -> SpedParseResult:
    """
    Parseia um arquivo SPED EFD ICMS/IPI completo.
    
    Args:
        file_path: Caminho para o arquivo .txt do SPED
        
    Returns:
        SpedParseResult com todos os registros organizados por bloco e tipo
    """
    result = SpedParseResult()
    result.filename = file_path.name

    # Calcular hash do arquivo
    with open(file_path, "rb") as f:
        result.file_hash = hashlib.sha256(f.read()).hexdigest()

    # Detectar encoding
    encoding = _detect_encoding(file_path)
    result.encoding_used = encoding

    # Ler e parsear linha por linha
    with open(file_path, "r", encoding=encoding) as f:
        for numero_linha, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha:
                continue

            result.file_info.total_linhas = numero_linha

            # Extrair tipo de registro
            campos_raw = linha.strip("|").split("|")
            if not campos_raw:
                result.erros_parse.append(f"Linha {numero_linha}: linha vazia ou malformada")
                continue

            reg_tipo = campos_raw[0]

            # Criar registro com campos mapeados se disponível
            registro = Registro(linha, numero_linha)
            if reg_tipo in REGISTRO_CLASSES:
                registro.CAMPOS = REGISTRO_CLASSES[reg_tipo]

            # Identificar bloco
            bloco = _identify_bloco(reg_tipo)

            # Armazenar no dict de registros por tipo
            if reg_tipo not in result.registros:
                result.registros[reg_tipo] = []
            result.registros[reg_tipo].append(registro)

            # Armazenar no dict de blocos
            if bloco not in result.blocos:
                result.blocos[bloco] = {}
            if reg_tipo not in result.blocos[bloco]:
                result.blocos[bloco][reg_tipo] = []
            result.blocos[bloco][reg_tipo].append(registro)

            # Contagem
            result.contagem_registros[reg_tipo] = result.contagem_registros.get(reg_tipo, 0) + 1

    # Extrair informações do registro 0000
    _extract_file_info(result)

    return result


def _extract_file_info(result: SpedParseResult):
    """Extrai informações do registro 0000 para o SpedFileInfo."""
    reg_0000 = result.get_registro_unico("0000")
    if not reg_0000:
        result.erros_parse.append("Registro 0000 não encontrado no arquivo!")
        return

    info = result.file_info

    # Campos do 0000 (índices padrão — layout v3.2.2)
    campos = reg_0000.campos_raw
    if len(campos) >= 2:
        info.cod_ver = campos[1] if len(campos) > 1 else ""
    if len(campos) >= 3:
        info.cod_fin = campos[2] if len(campos) > 2 else ""

    # Datas
    if len(campos) > 3 and len(campos[3]) == 8:
        try:
            info.dt_ini = date(int(campos[3][4:8]), int(campos[3][2:4]), int(campos[3][0:2]))
        except (ValueError, IndexError):
            pass
    if len(campos) > 4 and len(campos[4]) == 8:
        try:
            info.dt_fin = date(int(campos[4][4:8]), int(campos[4][2:4]), int(campos[4][0:2]))
        except (ValueError, IndexError):
            pass

    # Dados do contribuinte
    if len(campos) > 5:
        info.nome = campos[5]
    if len(campos) > 6:
        info.cnpj = campos[6]
    if len(campos) > 7:
        info.cpf = campos[7]
    if len(campos) > 8:
        info.uf = campos[8]
    if len(campos) > 9:
        info.ie = campos[9]
    if len(campos) > 10:
        info.cod_mun = campos[10]
    if len(campos) > 11:
        info.im = campos[11]
    if len(campos) > 12:
        info.suframa = campos[12]
    if len(campos) > 13:
        info.ind_perfil = campos[13]
    if len(campos) > 14:
        info.ind_ativ = campos[14]

    # Versão do layout
    info.layout_version = detect_layout_version(info.cod_ver) or "desconhecida"
    info.version_family = get_version_family(info.cod_ver)


def parse_sped_bytes(content: bytes, filename: str = "upload.txt") -> SpedParseResult:
    """
    Parseia conteúdo SPED a partir de bytes (útil para upload direto).
    """
    import tempfile
    import os

    # Salvar em arquivo temporário para reutilizar o parser
    tmp_path = Path(tempfile.mkdtemp()) / filename
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        result = parse_sped_file(tmp_path)
        result.filename = filename
        return result
    finally:
        os.unlink(tmp_path)
        os.rmdir(tmp_path.parent)
