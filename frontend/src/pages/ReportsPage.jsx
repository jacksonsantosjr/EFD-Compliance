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
            
            <div style={{ fontFamily: 'Inter, Arial, sans-serif', color: '#2D3A4A', backgroundColor: '#fff', padding: '32px', borderRadius: '8px', border: '1px solid var(--color-border)', overflowX: 'auto' }}>
                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                    <h1 style={{ color: '#6C5CE7', fontSize: '24px', fontWeight: 'bold', marginBottom: '8px' }}>DOSSIÊ TÉCNICO — EFD Compliance</h1>
                    <p style={{ color: '#666', fontStyle: 'italic', fontSize: '14px', borderBottom: '1px solid #DEE2E6', paddingBottom: '16px' }}>Validação Expert de SPED EFD ICMS/IPI — Análise Pós-PVA</p>
                </div>

                <h2 style={{ color: '#2D3A4A', fontSize: '18px', fontWeight: '600', marginTop: '32px', marginBottom: '16px', borderBottom: '2px solid #6C5CE7', paddingBottom: '4px' }}>1. Dados do Contribuinte</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', marginBottom: '24px' }}>
                    <tbody>
                        <tr><th style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left', backgroundColor: '#6C5CE7', color: 'white', fontWeight: '600', width: '30%' }}>Razão Social</th><td style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left' }}>{info.razao_social}</td></tr>
                        <tr style={{ backgroundColor: '#F8F9FA' }}><th style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left', backgroundColor: '#6C5CE7', color: 'white', fontWeight: '600' }}>CNPJ</th><td style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left' }}>{info.cnpj}</td></tr>
                        <tr><th style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left', backgroundColor: '#6C5CE7', color: 'white', fontWeight: '600' }}>Inscrição Estadual</th><td style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left' }}>{info.ie}</td></tr>
                        <tr style={{ backgroundColor: '#F8F9FA' }}><th style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left', backgroundColor: '#6C5CE7', color: 'white', fontWeight: '600' }}>Período</th><td style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left' }}>{info.periodo_ini} a {info.periodo_fin}</td></tr>
                        <tr><th style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left', backgroundColor: '#6C5CE7', color: 'white', fontWeight: '600' }}>Versão Layout</th><td style={{ border: '1px solid #DEE2E6', padding: '10px 12px', textAlign: 'left' }}>v{info.cod_ver} (Perfil {info.perfil})</td></tr>
                    </tbody>
                </table>

                <h2 style={{ color: '#2D3A4A', fontSize: '18px', fontWeight: '600', marginTop: '32px', marginBottom: '16px', borderBottom: '2px solid #6C5CE7', paddingBottom: '4px' }}>2. Score de Conformidade</h2>
                <div style={{ textAlign: 'center', margin: '24px 0', padding: '32px 24px', borderRadius: '8px', backgroundColor: '#F8F9FA', border: '1px solid #DEE2E6' }}>
                    <div style={{ fontSize: '42px', fontWeight: 'bold', marginBottom: '16px', color: score >= 80 ? '#00B894' : score >= 50 ? '#FDCB6E' : '#E17C80' }}>
                        {score.toFixed(1)}% — {score >= 80 ? 'BOM' : score >= 50 ? 'ATENÇÃO' : 'CRÍTICO'}
                    </div>
                    <div style={{ fontSize: '15px', color: '#666' }}>
                        ❌ <span style={{fontWeight: 'bold', color: '#E17C80'}}>{critical.length}</span> Críticos &nbsp;&nbsp; 
                        ⚠️ <span style={{fontWeight: 'bold', color: '#FDCB6E'}}>{findings.filter(f => f.severity === 'warning').length}</span> Atenção &nbsp;&nbsp; 
                        ℹ️ <span style={{fontWeight: 'bold', color: '#74B9FF'}}>{findings.filter(f => f.severity === 'info').length}</span> Informativos
                    </div>
                </div>

                <h2 style={{ color: '#2D3A4A', fontSize: '18px', fontWeight: '600', marginTop: '32px', marginBottom: '16px', borderBottom: '2px solid #6C5CE7', paddingBottom: '4px' }}>3. Achados Detalhados</h2>
                {findings.length === 0 ? (
                    <p style={{ color: '#00B894', fontWeight: 'bold' }}>✅ Nenhum achado estrutural ou matemático severo foi encontrado.</p>
                ) : (
                    findings.slice(0, 10).map((f, idx) => {
                        const isCritical = f.severity === 'critical';
                        const isWarn = f.severity === 'warning';
                        const color = isCritical ? '#E17C80' : isWarn ? '#FDCB6E' : '#74B9FF';
                        const icon = isCritical ? '❌' : isWarn ? '⚠️' : 'ℹ️';
                        
                        return (
                            <div key={idx} style={{ margin: '16px 0', padding: '16px', borderLeft: `4px solid ${color}`, backgroundColor: '#FAFAFA', borderRadius: '0 8px 8px 0', border: '1px solid #DEE2E6', borderLeftWidth: '4px' }}>
                                <p style={{ fontWeight: 'bold', fontSize: '15px', color: '#2D3A4A', marginBottom: '8px' }}>
                                    {icon} {f.title} <span style={{ color: '#999', fontSize: '13px' }}>[{f.code}]</span>
                                </p>
                                <p style={{ fontSize: '14px', marginBottom: '8px', color: '#444' }}>{f.description}</p>
                                {(f.expected_value || f.actual_value) && (
                                    <div style={{ fontSize: '13px', backgroundColor: '#fff', padding: '8px', borderRadius: '4px', border: '1px dashed #ccc', color: '#666' }}>
                                        <strong>Esperado:</strong> {f.expected_value || "N/D"} | <strong>Encontrado:</strong> {f.actual_value || "N/D"}
                                    </div>
                                )}
                            </div>
                        )
                    })
                )}
                {findings.length > 10 && (
                    <p style={{ textAlign: 'center', color: '#666', fontStyle: 'italic', marginTop: '16px' }}>
                        * Exibindo apenas os primeiros 10 achados. Exporte em DOCX/PDF para visualizar a lista completa.
                    </p>
                )}
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
