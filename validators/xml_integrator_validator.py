# -*- coding: utf-8 -*-
"""
Validador de Integração XML × EFD.
Cruza chaves de acesso e valores entre arquivos XML de NF-e e registros do SPED.
"""
from typing import List, Dict
from decimal import Decimal

from api.models.finding import Finding, Severity
from parser.sped_parser import SpedParseResult
from parser.xml_parser import NfeData


class XmlIntegratorValidator:
    """
    Cruza dados de XMLs de NF-e com os registros do SPED (principalmente Bloco C).
    """

    def __init__(self, parsed: SpedParseResult, xml_list: List[NfeData]):
        self.parsed = parsed
        self.xml_list = xml_list
        self.findings: List[Finding] = []

    def validate_all(self) -> List[Finding]:
        """Executa todas as regras de integração XML."""
        if not self.xml_list:
            return []

        self.findings = []
        
        # Mapear chaves presentes no SPED (C100, C113, etc.)
        sped_keys = self._get_all_sped_nfe_keys()
        
        # Mapear chaves presentes no SPED com seus valores para conferência
        sped_data_map = self._get_sped_nfe_data_map()

        for xml in self.xml_list:
            # Regra XML-001: Omissão de Nota Fiscal no SPED
            if xml.chave not in sped_keys:
                self.findings.append(Finding(
                    block="C",
                    register="C100",
                    severity=Severity.CRITICAL,
                    code="XML-001",
                    title="NF-e presente no XML mas ausente no SPED",
                    description=(
                        f"A NF-e chave {xml.chave} (Nº {xml.nNF}) foi encontrada nos arquivos XML enviados, "
                        f"mas não consta em nenhum registro de documento fiscal no SPED (C100, C113, etc.)."
                    ),
                    recommendation="Verifique se a nota foi omitida da escrituração ou se há erro na chave de acesso."
                ))
                continue # Se não está no SPED, não dá pra comparar valores

            # Regra XML-002: Divergência de Valores
            if xml.chave in sped_data_map:
                sped_val = sped_data_map[xml.chave]["valor"]
                if abs(float(sped_val) - xml.vNF) > 0.01:
                    self.findings.append(Finding(
                        block="C",
                        register="C100",
                        severity=Severity.CRITICAL,
                        code="XML-002",
                        title="Divergência de valor total entre XML e SPED",
                        description=(
                            f"A NF-e chave {xml.chave} possui valor total de R$ {xml.vNF:.2f} no XML, "
                            f"porém foi escriturada no SPED com o valor de R$ {float(sped_val):.2f}."
                        ),
                        recommendation="Corrija o valor escriturado no registro C100 para corresponder ao XML da nota fiscal."
                    ))

            # Regra XML-003: NF-e Cancelada no XML mas Regular no SPED
            if xml.status == "2": # Cancelada
                sped_sit = sped_data_map.get(xml.chave, {}).get("situacao", "")
                if sped_sit == "00": # 00=Documento regular
                    self.findings.append(Finding(
                        block="C",
                        register="C100",
                        severity=Severity.WARNING,
                        code="XML-003",
                        title="NF-e cancelada no XML mas regular no SPED",
                        description=(
                            f"A NF-e chave {xml.chave} consta como cancelada nos arquivos XML, "
                            f"mas está escriturada como 'Documento Regular' (CST 00) no SPED."
                        ),
                        recommendation="Verifique se a nota foi realmente cancelada e retifique o código de situação (COD_SIT) no SPED."
                    ))

        return self.findings

    def _get_all_sped_nfe_keys(self) -> set:
        """Coleta todas as chaves de NF-e citadas no SPED."""
        keys = set()
        
        # Chaves no C100
        for reg in self.parsed.get_registros("C100"):
            chave = reg.get_campo("CHV_NFE")
            if chave:
                keys.add(chave)
                
        # Chaves no C113 (Documentos Referenciados)
        for reg in self.parsed.get_registros("C113"):
            chave = reg.get_campo("CHV_NFE")
            if chave:
                keys.add(chave)
                
        return keys

    def _get_sped_nfe_data_map(self) -> Dict[str, Dict]:
        """Mapeia chaves para seus dados de valor e situação no SPED."""
        data_map = {}
        
        # Prioridade para C100
        for reg in self.parsed.get_registros("C100"):
            chave = reg.get_campo("CHV_NFE")
            if chave:
                data_map[chave] = {
                    "valor": reg.get_campo("VL_DOC") or "0",
                    "situacao": reg.get_campo("COD_SIT") or "00"
                }
                
        return data_map
