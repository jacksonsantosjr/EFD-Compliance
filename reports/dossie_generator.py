# -*- coding: utf-8 -*-
"""
Gerador principal de dossiê técnico.
Coordena a geração do dossiê em DOCX e PDF a partir do AnalysisResult.
"""
from pathlib import Path
from typing import Optional

from api.models.sped_file import AnalysisResult
from api.config import REPORTS_OUTPUT_DIR


class DossieGenerator:
    """
    Gerador de dossiê técnico do EFD Compliance.
    Recebe um AnalysisResult e gera relatório estruturado.
    """

    def __init__(self, analysis: AnalysisResult):
        self.analysis = analysis
        self.output_dir = REPORTS_OUTPUT_DIR

    def generate_docx(self, output_path: Optional[Path] = None) -> Path:
        """Gera dossiê em formato DOCX."""
        from reports.docx_builder import DocxBuilder

        if output_path is None:
            filename = self._build_filename("docx")
            output_path = self.output_dir / filename

        builder = DocxBuilder(self.analysis)
        builder.build()
        builder.save(output_path)

        return output_path

    def generate_pdf(self, output_path: Optional[Path] = None) -> Path:
        """Gera dossiê em formato PDF."""
        from reports.pdf_builder import PdfBuilder

        if output_path is None:
            filename = self._build_filename("pdf")
            output_path = self.output_dir / filename

        builder = PdfBuilder(self.analysis)
        builder.build()
        builder.save(output_path)

        return output_path

    def _build_filename(self, extension: str) -> str:
        """Constrói nome do arquivo baseado nos dados da análise."""
        info = self.analysis.file_info
        cnpj_clean = info.cnpj.replace(".", "").replace("/", "").replace("-", "")
        periodo = ""
        if info.periodo_ini:
            periodo = info.periodo_ini.strftime("%m%Y")
        return f"dossie_{cnpj_clean}_{periodo}_{self.analysis.id[:8]}.{extension}"
