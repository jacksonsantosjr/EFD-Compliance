function ScoreGauge({ score }) {
  const radius = 65
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  let color, label
  if (score >= 91) {
    color = 'var(--color-score-excellent)'
    label = 'EXCELENTE'
  } else if (score >= 71) {
    color = 'var(--color-score-good)'
    label = 'BOM'
  } else if (score >= 51) {
    color = 'var(--color-score-reasonable)'
    label = 'RAZOÁVEL'
  } else if (score >= 41) {
    color = 'var(--color-score-medium)'
    label = 'ATENÇÃO'
  } else if (score >= 21) {
    color = 'var(--color-score-bad)'
    label = 'CRÍTICO'
  } else {
    color = 'var(--color-score-inadequate)'
    label = 'INADEQUADO'
  }

  return (
    <div className="score-gauge">
      <div className="score-circle">
        <svg width="160" height="160">
          <circle
            className="score-bg"
            cx="80" cy="80" r={radius}
            fill="none"
            strokeWidth="10"
          />
          <circle
            className="score-fill"
            cx="80" cy="80" r={radius}
            fill="none"
            strokeWidth="10"
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="score-value" style={{ color }}>
          {score.toFixed(1)}%
        </div>
      </div>
      <div className="score-label" style={{ color }}>
        {label}
      </div>
    </div>
  )
}

export default ScoreGauge
