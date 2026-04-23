# -*- coding: utf-8 -*-
"""
Parser de XML para NF-e (Modelo 55).
Extrai campos essenciais para cruzamento com o SPED.
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class NfeData:
    chave: str
    nNF: str
    serie: str
    dhEmi: datetime
    cnpj_emit: str
    cnpj_dest: str
    vNF: float
    status: str = "1"  # 1=Autorizada, 2=Cancelada (simplificado)


def parse_nfe_xml(content: bytes) -> Optional[NfeData]:
    """
    Parseia o XML de uma NF-e e retorna um objeto NfeData.
    Suporta XMLs de distribuição (com protNFe) ou apenas a nota.
    """
    try:
        # Remover namespaces para facilitar a busca
        root = ET.fromstring(content)
        
        # O namespace da NF-e geralmente é http://www.portalfiscal.inf.br/nfe
        # Usaremos busca ignorando namespace ou tratando explicitamente
        ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
        
        infNFe = root.find(".//ns:infNFe", ns)
        if infNFe is None:
            return None
            
        chave = infNFe.get("Id", "")[3:]  # Remove o prefixo 'NFe'
        
        ide = infNFe.find("ns:ide", ns)
        emit = infNFe.find("ns:emit", ns)
        dest = infNFe.find("ns:dest", ns)
        total = infNFe.find("ns:total/ns:ICMSTot", ns)
        
        if any(x is None for x in [ide, emit, dest, total]):
            return None
            
        # Data de emissão (trata formatos com e sem fuso horário)
        dhEmi_raw = ide.findtext("ns:dhEmi", default="", namespaces=ns)
        if not dhEmi_raw:
            dhEmi_raw = ide.findtext("ns:dEmi", default="", namespaces=ns) # Versões antigas
            
        try:
            # Tenta parsear ISO format (2024-04-22T17:35:00-03:00)
            if "T" in dhEmi_raw:
                # Remove fuso se houver para simplificar comparação básica
                dhEmi = datetime.fromisoformat(dhEmi_raw.split("-")[0] if "-" in dhEmi_raw and len(dhEmi_raw) > 20 else dhEmi_raw)
            else:
                dhEmi = datetime.strptime(dhEmi_raw, "%Y-%m-%d")
        except:
            dhEmi = datetime.now()

        # Status: verifica se há informação de cancelamento (simplificado)
        # Em um sistema real, verificaríamos o protNFe ou eventos
        status = "1"
        if b"retCancNFe" in content or b"procEventoNFe" in content and b"<tpEvento>110111" in content:
            status = "2" # Cancelada

        return NfeData(
            chave=chave,
            nNF=ide.findtext("ns:nNF", namespaces=ns),
            serie=ide.findtext("ns:serie", namespaces=ns),
            dhEmi=dhEmi,
            cnpj_emit=emit.findtext("ns:CNPJ", namespaces=ns) or emit.findtext("ns:CPF", namespaces=ns),
            cnpj_dest=dest.findtext("ns:CNPJ", namespaces=ns) or dest.findtext("ns:CPF", namespaces=ns),
            vNF=float(total.findtext("ns:vNF", default="0", namespaces=ns)),
            status=status
        )
    except Exception as e:
        print(f"Erro ao parsear XML: {e}")
        return None
