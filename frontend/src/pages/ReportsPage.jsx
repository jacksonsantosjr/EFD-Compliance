import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { exportReport } from '../services/api'
import Modal from '../components/Modal'

function ReportsPage() {
  const [result, setResult] = useState(null)
  const [exportingType, setExportingType] = useState(null)
  const [modalData, setModalData] = useState({ isOpen: false, title: '', message: '' })
  const navigate = useNavigate()

  useEffect(() => {
    const stored = sessionStorage.getItem('analysisResult')
    if (stored) {
      setResult(JSON.parse(stored))
    }
  }, [])

  if (!result) {
    return (
      <div className="text-center" style={{ padding: 'var(--space-12)' }}>
        <h2 style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--space-4)' }}>
          Nenhum dossiê disponível
        </h2>
        <p style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--space-6)' }}>
          Faça o upload de um arquivo SPED para gerar e visualizar o dossiê detalhado.
        </p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          📤 Ir para Upload
        </button>
      </div>
    )
  }

  const handleExport = async (format) => {
    setExportingType(format)
    try {
      const razao = result.file_info.razao_social.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase()
      const perIni = result.file_info.periodo_ini.replace(/\//g, '')
      const perFin = result.file_info.periodo_fin.replace(/\//g, '')
      const fileName = `dossie_${razao}_${perIni}_${perFin}`
      await exportReport(result.id, format, fileName)
      
      // Delay de 3s para que o modal não apareça antes do diálogo de "Salvar Como" do navegador
      setTimeout(() => {
        setModalData({
          isOpen: true,
          title: '✅ Sucesso',
          message: `O relatório no formato ${format.toUpperCase()} foi gerado e o download iniciado.`
        })
      }, 3000)
    } catch (err) {
      setModalData({
        isOpen: true,
        title: '❌ Erro na Exportação',
        message: err.message
      })
    } finally {
      setExportingType(null)
    }
  }

  const { file_info: info, score, findings = [] } = result
  const critical = findings.filter(f => f.severity === 'critical')

  return (
    <div>
      <div className="card mb-6">
        <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <h2 style={{ fontWeight: 'var(--font-weight-bold)', fontSize: 'var(--font-size-lg)' }}>
              Exportação do Dossiê Técnico
            </h2>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
              Selecione o formato desejado para salvar o parecer oficial de auditoria.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button className="btn" style={{backgroundColor: '#1E88E5', color: '#fff'}} onClick={() => handleExport('docx')} disabled={exportingType !== null}>
              📄 {exportingType === 'docx' ? 'Gerando DOCX...' : 'Exportar em DOCX'}
            </button>
            <button className="btn" style={{backgroundColor: '#E53935', color: '#fff'}} onClick={() => handleExport('pdf')} disabled={exportingType !== null}>
              📑 {exportingType === 'pdf' ? 'Gerando PDF...' : 'Exportar em PDF'}
            </button>
          </div>
        </div>
      </div>

      <div className="card">
         <div className="card-body">
            <h3 style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
                Visualização Prévia do Dossiê Interativo
            </h3>
            
            <div style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--color-text-secondary)', backgroundColor: 'var(--color-bg-primary)', padding: 'var(--space-4)', borderRadius: 'var(--radius)', border: '1px solid var(--color-border)' }}>
{`============================================================
DOSSIÊ TÉCNICO DE AUDITORIA SPED - EFD ICMS/IPI
============================================================

Razão Social  : ${info.razao_social}
CNPJ          : ${info.cnpj}
Inscrição Est.: ${info.ie}
Período       : ${info.periodo_ini} a ${info.periodo_fin}
Layout        : v${info.cod_ver} (Perfil ${info.perfil})

============================================================
1. RESULTADO GERAL DA AVALIAÇÃO
============================================================
>> SCORE DE CONFORMIDADE: ${score.toFixed(1)} / 100
>> STATUS GERAL: ${score >= 90 ? 'ALTO NÍVEL DE CONFORMIDADE' : score >= 70 ? 'ATENÇÃO REQUERIDA' : 'RISCO FISCAL ALTO'}

Resumo de Ocorrências:
- Críticas : ${critical.length} itens (Impacto direto em apuração)
- Alertas  : ${findings.filter(f => f.severity === 'warning').length} itens (Risco secundário)
- Info     : ${findings.filter(f => f.severity === 'info').length} itens (Melhorias sugeridas)

============================================================
2. DESTAQUE DOS ACHADOS CRÍTICOS
============================================================
${critical.length > 0 
  ? critical.map(f => `[${f.code}] ${f.title}\n  -> ${f.description}\n`).join('\n')
  : '✅ Nenhum achado estrutural ou matemático severo foi encontrado.\n'}
============================================================
* Observação: Extraia o relatório em DOCX/PDF para ver 
todas as seções detalhadas, incluindo os testes de 
Obrigações Acessórias e Consistência Tributária (CIAP, DIFAL).
============================================================
`}
            </div>
         </div>
      </div>

      <Modal 
        isOpen={modalData.isOpen} 
        title={modalData.title} 
        onClose={() => setModalData(prev => ({ ...prev, isOpen: false }))}
      >
        {modalData.message}
      </Modal>
    </div>
  )
}

export default ReportsPage
