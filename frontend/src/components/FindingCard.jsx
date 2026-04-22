function FindingCard({ finding }) {
  const severityClass = `finding-${finding.severity}`
  const severityIcons = { critical: '❌', warning: '⚠️', info: 'ℹ️' }
  const severityLabels = { critical: 'CRÍTICO', warning: 'ATENÇÃO', info: 'INFO' }
  const badgeClass = `badge badge-${finding.severity}`

  return (
    <div className={`finding-item ${severityClass}`}>
      <div className="finding-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span>{severityIcons[finding.severity]}</span>
          <span className="finding-title">{finding.title}</span>
        </div>
        <span className="finding-code">{finding.code}</span>
      </div>

      {finding.description && (
        <div className="finding-description">{finding.description}</div>
      )}

      {(finding.expected_value || finding.actual_value) && (
        <div className="finding-meta">
          {finding.expected_value && (
            <span>✅ Esperado: <strong>{finding.expected_value}</strong></span>
          )}
          {finding.actual_value && (
            <span>❌ Encontrado: <strong>{finding.actual_value}</strong></span>
          )}
        </div>
      )}

      <div className="finding-meta">
        {finding.legal_reference && (
          <span>📖 {finding.legal_reference}</span>
        )}
        {finding.recommendation && (
          <span>💡 {finding.recommendation}</span>
        )}
      </div>
    </div>
  )
}

export default FindingCard
