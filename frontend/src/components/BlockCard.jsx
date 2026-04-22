function BlockCard({ code, summary, onClick }) {
  const statusIcons = { ok: '✅', warning: '⚠️', critical: '❌' }

  const handleClick = () => {
    if (onClick && (summary.status === 'critical' || summary.status === 'warning')) {
      onClick(code)
    }
  }

  const isClickable = summary.status === 'critical' || summary.status === 'warning'

  return (
    <div 
      className={`block-card status-${summary.status}`} 
      onClick={handleClick}
      style={{ cursor: isClickable ? 'pointer' : 'default', opacity: isClickable ? 1 : 0.8 }}
      title={isClickable ? "Clique para ver detalhes" : "Nenhum alerta crítico ou atenção"}
    >
      <div className="block-code">
        {statusIcons[summary.status]} {code}
      </div>
      <div className="block-name">{summary.block_name}</div>
      <div className="block-count">
        {summary.total_records} registros
      </div>
      <div style={{ marginTop: 'var(--space-2)', display: 'flex', justifyContent: 'center', gap: 'var(--space-2)' }}>
        {summary.findings_critical > 0 && (
          <span className="badge badge-critical">{summary.findings_critical}</span>
        )}
        {summary.findings_warning > 0 && (
          <span className="badge badge-warning">{summary.findings_warning}</span>
        )}
        {summary.findings_info > 0 && (
          <span className="badge badge-info">{summary.findings_info}</span>
        )}
      </div>
    </div>
  )
}

export default BlockCard
