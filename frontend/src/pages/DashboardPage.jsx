import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ScoreGauge from '../components/ScoreGauge'
import FindingCard from '../components/FindingCard'
import BlockCard from '../components/BlockCard'
import { exportReport } from '../services/api'

function DashboardPage() {
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [exporting, setExporting] = useState(false)
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
          Nenhuma análise disponível
        </h2>
        <p style={{ color: 'var(--color-text-tertiary)', marginBottom: 'var(--space-6)' }}>
          Faça o upload de um arquivo SPED para visualizar os resultados.
        </p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          📤 Ir para Upload
        </button>
      </div>
    )
  }

  const info = result.file_info
  const findings = result.findings || []
  const blockSummaries = result.block_summaries || {}

  const totalCritical = findings.filter(f => f.severity === 'critical').length
  const totalWarning = findings.filter(f => f.severity === 'warning').length
  const totalInfo = findings.filter(f => f.severity === 'info').length

  const filteredFindings = severityFilter === 'all'
    ? findings
    : findings.filter(f => f.severity === severityFilter)

  const handleExport = async (format) => {
    setExporting(true)
    try {
      await exportReport(result.id, format)
    } catch (err) {
      alert('Erro ao gerar relatório: ' + err.message)
    } finally {
      setExporting(false)
    }
  }

  const formatCnpj = (cnpj) => {
    const c = (cnpj || '').replace(/\D/g, '')
    if (c.length === 14) return `${c.slice(0,2)}.${c.slice(2,5)}.${c.slice(5,8)}/${c.slice(8,12)}-${c.slice(12)}`
    return cnpj
  }

  return (
    <div>
      {/* Cabeçalho do Contribuinte */}
      <div className="card mb-6">
        <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <h2 style={{ fontWeight: 'var(--font-weight-bold)', fontSize: 'var(--font-size-lg)' }}>
              {info.razao_social}
            </h2>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
              CNPJ: {formatCnpj(info.cnpj)} &nbsp;|&nbsp; IE: {info.ie} &nbsp;|&nbsp; UF: {info.uf}
            </div>
            <div style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)', marginTop: 'var(--space-1)' }}>
              Período: {info.periodo_ini} a {info.periodo_fin} &nbsp;|&nbsp; Perfil {info.perfil} &nbsp;|&nbsp; Layout v{info.cod_ver}
            </div>
          </div>
        </div>
      </div>

      {/* Score + Stats */}
      <div className="grid-2 mb-6">
        <div className="card">
          <div className="card-body text-center">
            <h3 style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)' }}>
              Score de Conformidade
            </h3>
            <ScoreGauge score={result.score || 0} />
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <h3 style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)' }}>
              Resumo
            </h3>
            <div className="stats-grid">
              <div className="stat-card stat-critical">
                <div className="stat-value">{totalCritical}</div>
                <div className="stat-label">Críticos</div>
              </div>
              <div className="stat-card stat-warning">
                <div className="stat-value">{totalWarning}</div>
                <div className="stat-label">Atenção</div>
              </div>
              <div className="stat-card stat-info">
                <div className="stat-value">{totalInfo}</div>
                <div className="stat-label">Informativos</div>
              </div>
              <div className="stat-card stat-success">
                <div className="stat-value">{result.total_registros?.toLocaleString('pt-BR')}</div>
                <div className="stat-label">Registros</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 'var(--space-1)', marginBottom: 'var(--space-4)' }}>
        {[
          { key: 'overview', label: '📊 Blocos', id: 'tab-blocks' },
          { key: 'findings', label: '🔍 Achados', id: 'tab-findings' },
        ].map(tab => (
          <button
            key={tab.key}
            id={tab.id}
            className={`btn ${activeTab === tab.key ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Blocos */}
      {activeTab === 'overview' && (
        <div className="blocks-grid">
          {Object.entries(blockSummaries)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([code, summary]) => (
              <BlockCard key={code} code={code} summary={summary} />
            ))
          }
        </div>
      )}

      {/* Tab: Achados */}
      {activeTab === 'findings' && (
        <div>
          {/* Filtro */}
          <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
            {[
              { key: 'all', label: `Todos (${findings.length})` },
              { key: 'critical', label: `❌ Críticos (${totalCritical})` },
              { key: 'warning', label: `⚠️ Atenção (${totalWarning})` },
              { key: 'info', label: `ℹ️ Info (${totalInfo})` },
            ].map(f => (
              <button
                key={f.key}
                className={`btn ${severityFilter === f.key ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSeverityFilter(f.key)}
                style={{ fontSize: 'var(--font-size-sm)' }}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Lista */}
          {filteredFindings.length === 0 ? (
            <div className="card">
              <div className="card-body text-center" style={{ color: 'var(--color-text-tertiary)' }}>
                ✅ Nenhum achado encontrado para este filtro.
              </div>
            </div>
          ) : (
            filteredFindings.map(finding => (
              <FindingCard key={finding.id} finding={finding} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default DashboardPage
