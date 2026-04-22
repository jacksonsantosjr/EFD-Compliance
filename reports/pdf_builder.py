# -*- coding: utf-8 -*-
"""
Builder de dossiê PDF — gera relatório técnico em PDF.
Utiliza HTML como intermediário e WeasyPrint para converter.
"""
from pathlib import Path
from datetime import datetime
from decimal import Decimal

from api.models.sped_file import AnalysisResult
from api.models.finding import Finding, Severity


# Importações condicionais
try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


SEVERITY_ICONS = {
    Severity.CRITICAL: "❌",
    Severity.WARNING: "⚠️",
    Severity.INFO: "ℹ️",
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "CRÍTICO",
    Severity.WARNING: "ATENÇÃO",
    Severity.INFO: "INFORMATIVO",
}

SEVERITY_COLORS = {
    Severity.CRITICAL: "#E17C80",
    Severity.WARNING: "#FDCB6E",
    Severity.INFO: "#74B9FF",
}

STATUS_ICONS = {
    "ok": "✅",
    "warning": "⚠️",
    "critical": "❌",
}


class PdfBuilder:
    """Constrói o dossiê técnico em formato PDF via HTML."""

    def __init__(self, analysis: AnalysisResult):
        self.analysis = analysis
        self.html_content = ""

    def build(self):
        """Constrói o HTML completo do dossiê."""
        sections = [
            self._css(),
            self._header(),
            self._quadro_resumo(),
            self._score_section(),
            self._block_overview(),
            self._findings_section(),
            self._action_plan(),
            self._footer(),
        ]

        body = "\n".join(sections)
        self.html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Dossiê Técnico — EFD Compliance</title>
</head>
<body>
{body}
</body>
</html>"""

    def save(self, path: Path):
        """Salva o documento PDF."""
        if not HAS_WEASYPRINT:
            # Fallback: salvar como HTML
            html_path = path.with_suffix('.html')
            html_path.write_text(self.html_content, encoding='utf-8')
            raise ImportError(
                f"WeasyPrint não instalado. HTML salvo em: {html_path}\n"
                "Execute: pip install weasyprint"
            )

        HTML(string=self.html_content).write_pdf(str(path))

    def _css(self) -> str:
        """CSS do relatório."""
        return """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }
    @page {
        margin: 1.5cm;
        size: A4;
    }
    body {
        font-family: 'Inter', 'Calibri', 'Noto Color Emoji', 'Segoe UI Emoji', sans-serif;
        font-size: 10pt;
        color: #2D3A4A;
        line-height: 1.4;
    }
    h1 { color: #6C5CE7; font-size: 20pt; margin-bottom: 8px; text-align: center; }
    h2 { color: #2D3A4A; font-size: 14pt; margin-top: 20px; margin-bottom: 10px;
         border-bottom: 2px solid #6C5CE7; padding-bottom: 4px; }
    h3 { color: #6C5CE7; font-size: 12pt; margin-top: 14px; margin-bottom: 6px; }
    .subtitle { text-align: center; color: #666; font-style: italic; margin-bottom: 20px; }
    .score-box {
        text-align: center; margin: 20px 0; padding: 20px;
        border-radius: 8px; background: #F8F9FA;
    }
    .score-value { font-size: 32pt; font-weight: 700; }
    .score-good { color: #00B894; }
    .score-warn { color: #FDCB6E; }
    .score-bad { color: #E17C80; }
    .totals { font-size: 11pt; margin-top: 8px; }
    table {
        width: 100%; border-collapse: collapse; margin: 10px 0;
        font-size: 9pt;
    }
    th, td {
        border: 1px solid #DEE2E6; padding: 6px 8px; text-align: left;
    }
    th { background: #6C5CE7; color: white; font-weight: 600; }
    tr:nth-child(even) { background: #F8F9FA; }
    .finding { margin: 12px 0; padding: 10px; border-left: 4px solid #ccc; background: #FAFAFA; }
    .finding-critical { border-left-color: #E17C80; }
    .finding-warning { border-left-color: #FDCB6E; }
    .finding-info { border-left-color: #74B9FF; }
    .finding-title { font-weight: 700; font-size: 10pt; }
    .finding-code { color: #999; font-size: 8pt; }
    .finding-ref { color: #74B9FF; font-size: 8pt; font-style: italic; }
    .finding-rec { color: #00B894; font-size: 9pt; }
    .footer {
        margin-top: 40px; padding-top: 10px; border-top: 1px solid #DEE2E6;
        text-align: center; color: #999; font-size: 8pt;
    }
    .action-item { margin: 4px 0; padding: 4px 0; }
    .page-break { page-break-before: always; }
</style>"""

    def _header(self) -> str:
        return """<h1>DOSSIÊ TÉCNICO — EFD Compliance</h1>
<p class="subtitle">Validação Expert de SPED EFD ICMS/IPI — Análise Pós-PVA</p>"""

    def _quadro_resumo(self) -> str:
        info = self.analysis.file_info
        cnpj = self._format_cnpj(info.cnpj)
        periodo_ini = info.periodo_ini.strftime('%d/%m/%Y') if info.periodo_ini else 'N/D'
        periodo_fin = info.periodo_fin.strftime('%d/%m/%Y') if info.periodo_fin else 'N/D'

        return f"""<h2>1. Dados do Contribuinte</h2>
<table>
    <tr><th style="width:30%">Razão Social</th><td>{info.razao_social}</td></tr>
    <tr><th>CNPJ</th><td>{cnpj}</td></tr>
    <tr><th>Inscrição Estadual</th><td>{info.ie}</td></tr>
    <tr><th>UF</th><td>{info.uf}</td></tr>
    <tr><th>Período</th><td>{periodo_ini} a {periodo_fin}</td></tr>
    <tr><th>Perfil</th><td>Perfil {info.perfil}</td></tr>
    <tr><th>Versão Layout</th><td>{info.cod_ver}</td></tr>
    <tr><th>Arquivo</th><td>{self.analysis.filename}</td></tr>
</table>"""

    def _score_section(self) -> str:
        score = self.analysis.score
        if score >= 80:
            cls = "score-good"
            label = "BOM"
        elif score >= 50:
            cls = "score-warn"
            label = "ATENÇÃO"
        else:
            cls = "score-bad"
            label = "CRÍTICO"

        tc = self.analysis.total_critical
        tw = self.analysis.total_warnings
        ti = self.analysis.total_info

        return f"""<h2>2. Score de Conformidade</h2>
<div class="score-box">
    <div class="score-value {cls}">{score:.1f}% — {label}</div>
    <div class="totals">
        ❌ {tc} Críticos &nbsp;&nbsp; ⚠️ {tw} Atenção &nbsp;&nbsp; ℹ️ {ti} Informativos
    </div>
</div>"""

    def _block_overview(self) -> str:
        rows = ""
        for code, s in sorted(self.analysis.block_summaries.items()):
            icon = STATUS_ICONS.get(s.status, "")
            rows += f"<tr><td>{code}</td><td>{s.block_name}</td><td>{s.total_records}</td><td>{s.total_findings}</td><td>{icon}</td></tr>\n"

        return f"""<h2>3. Visão por Bloco</h2>
<table>
    <tr><th>Bloco</th><th>Descrição</th><th>Registros</th><th>Achados</th><th>Status</th></tr>
    {rows}
</table>"""

    def _findings_section(self) -> str:
        if not self.analysis.findings:
            return "<h2>4. Achados Detalhados</h2><p>Nenhum achado identificado. ✅</p>"

        html = '<h2 class="page-break">4. Achados Detalhados</h2>\n'

        for severity in [Severity.CRITICAL, Severity.WARNING, Severity.INFO]:
            findings = [f for f in self.analysis.findings if f.severity == severity]
            if not findings:
                continue

            icon = SEVERITY_ICONS[severity]
            label = SEVERITY_LABELS[severity]
            html += f'<h3>{icon} {label} ({len(findings)})</h3>\n'

            for f in findings:
                css_class = f"finding-{severity.value}"
                values = ""
                if f.expected_value or f.actual_value:
                    values = f'<p><strong>Esperado:</strong> {f.expected_value or "N/D"} | <strong>Encontrado:</strong> {f.actual_value or "N/D"}</p>'
                ref = f'<p class="finding-ref">📖 {f.legal_reference}</p>' if f.legal_reference else ""
                rec = f'<p class="finding-rec">💡 {f.recommendation}</p>' if f.recommendation else ""

                html += f"""<div class="finding {css_class}">
    <p class="finding-title">{f.title} <span class="finding-code">[{f.code}]</span></p>
    <p>{f.description}</p>
    {values}{ref}{rec}
</div>\n"""

        return html

    def _action_plan(self) -> str:
        critical = [f for f in self.analysis.findings if f.severity == Severity.CRITICAL]
        warnings = [f for f in self.analysis.findings if f.severity == Severity.WARNING]
        if not critical and not warnings:
            return ""

        html = '<h2>5. Plano de Ação</h2>\n'

        if critical:
            html += '<h3>Ações Imediatas (Críticas)</h3>\n<ol>\n'
            for f in critical:
                rec = f.recommendation or "Verificar e corrigir."
                html += f'<li class="action-item"><strong>[{f.code}]</strong> {rec}</li>\n'
            html += '</ol>\n'

        if warnings:
            html += '<h3>Ações Recomendadas</h3>\n<ol>\n'
            for f in warnings:
                rec = f.recommendation or "Analisar."
                html += f'<li class="action-item"><strong>[{f.code}]</strong> {rec}</li>\n'
            html += '</ol>\n'

        return html

    def _footer(self) -> str:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        return f"""<div class="footer">
    Dossiê gerado por EFD Compliance v{self.analysis.validator_version}<br>
    Data: {now} | Hash: {self.analysis.file_hash[:16]}...
</div>"""

    @staticmethod
    def _format_cnpj(cnpj: str) -> str:
        cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
