# -*- coding: utf-8 -*-
import asyncio
from pathlib import Path
from parser.sped_parser import parse_sped_bytes
from parser.xml_parser import parse_nfe_xml
from validators.base_validator import BaseValidator

# 1. Simular XML de NF-e
xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <NFe>
        <infNFe Id="NFe35240400000000000000550010000001231000001234" versao="4.00">
            <ide>
                <nNF>123</nNF>
                <serie>1</serie>
                <dhEmi>2024-04-22T10:00:00-03:00</dhEmi>
            </ide>
            <emit><CNPJ>12345678000199</CNPJ></emit>
            <dest><CNPJ>98765432000188</CNPJ></dest>
            <total><ICMSTot><vNF>1500.00</vNF></ICMSTot></total>
        </infNFe>
    </NFe>
</nfeProc>"""

# 2. Simular SPED (Sem a nota acima para gerar erro de omissão)
sped_content = b"""|0000|015|0|01012024|31012024|EMPRESA TESTE|12345678000199||SP|123456789|3550308|||A|1|
|0001|0|
|9999|3|
"""

async def test_integration():
    print("Iniciando teste de integração Fase 2...")
    
    # Parse XML
    nfe_data = parse_nfe_xml(xml_content)
    print(f"XML Parseado: Chave={nfe_data.chave}, Valor={nfe_data.vNF}")
    
    # Parse SPED
    parsed_sped = parse_sped_bytes(sped_content, "test.txt")
    
    # Validar
    validator = BaseValidator(parsed_sped, xml_data=[nfe_data])
    result = await validator.validate()
    
    print(f"Total de Achados: {len(result.findings)}")
    for f in result.findings:
        if f.code.startswith("XML"):
            print(f"[{f.severity}] {f.code}: {f.title}")
            print(f"Descrição: {f.description}")

if __name__ == "__main__":
    asyncio.run(test_integration())
