# -*- coding: utf-8 -*-
"""
Parser principal da Escrituração Contábil Digital (ECD).
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date

from parser.registro import Registro

class EcdFileInfo:
    """Informações extraídas do registro 0000 da ECD."""
    def __init__(self):
        self.dt_ini: Optional[date] = None
        self.dt_fin: Optional[date] = None
        self.nome: str = ""
        self.cnpj: str = ""
        self.uf: str = ""
        self.ie: str = ""
        self.cod_mun: str = ""
        self.im: str = ""
        self.total_linhas: int = 0


class EcdParseResult:
    """Resultado do parsing de um arquivo ECD."""
    def __init__(self):
        self.file_info = EcdFileInfo()
        self.file_hash: str = ""
        self.filename: str = ""
        self.registros: Dict[str, List[Registro]] = {}
        self.erros_parse: List[str] = []
        self.total_registros: int = 0

    def get_registros(self, tipo: str) -> List[Registro]:
        return self.registros.get(tipo, [])

    def get_registro_unico(self, tipo: str) -> Optional[Registro]:
        regs = self.registros.get(tipo, [])
        return regs[0] if regs else None


def parse_ecd_file(file_path: str) -> EcdParseResult:
    """
    Lê o arquivo TXT da ECD e organiza os registros.
    """
    path = Path(file_path)
    result = EcdParseResult()
    
    if not path.exists():
        result.erros_parse.append(f"Arquivo não encontrado: {file_path}")
        return result
        
    # Tenta descobrir o encoding
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin1") as f:
            lines = f.readlines()
            
    result.file_info.total_linhas = len(lines)
    result.total_registros = len(lines)
    
    for num_linha, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line == "|":
            continue
            
        fields = line.split("|")
        if len(fields) < 2:
            continue
            
        # Posição 1 é o tipo (ex: 0000, I200)
        tipo_registro = fields[1]
        
        reg = Registro(tipo=tipo_registro, campos=fields, num_linha=num_linha)
        
        if tipo_registro not in result.registros:
            result.registros[tipo_registro] = []
        result.registros[tipo_registro].append(reg)
        
        # População do cabeçalho da ECD
        # Layout ECD 0000: |0000|LECD|DT_INI|DT_FIN|NOME|CNPJ|UF|IE|COD_MUN|IM|IND_SIT_ESP|...
        if tipo_registro == "0000":
            try:
                if len(fields) > 4:
                    result.file_info.nome = fields[4]
                if len(fields) > 5:
                    result.file_info.cnpj = fields[5]
                if len(fields) > 6:
                    result.file_info.uf = fields[6]
                
                # Conversão de datas
                if len(fields) > 2 and fields[2]:
                    result.file_info.dt_ini = datetime.strptime(fields[2], "%d%m%Y").date()
                if len(fields) > 3 and fields[3]:
                    result.file_info.dt_fin = datetime.strptime(fields[3], "%d%m%Y").date()
            except Exception as e:
                result.erros_parse.append(f"Erro ao fazer o parse do cabeçalho ECD 0000: {str(e)}")
                
    return result
