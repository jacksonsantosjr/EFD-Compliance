import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadSpedFile } from '../services/api'

function UploadPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()
  const navigate = useNavigate()

  useEffect(() => {
    let interval;
    if (loading) {
      setProgress(0)
      interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev + 0.5 // Slow down at the end
          return prev + 5 // Fast at the beginning
        })
      }, 500)
    } else {
      setProgress(0)
    }
    return () => clearInterval(interval)
  }, [loading])

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => setDragging(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.name.endsWith('.txt')) {
      setFile(droppedFile)
      setError(null)
    } else {
      setError('Formato inválido. Envie um arquivo .txt do SPED EFD.')
    }
  }

  const handleSelect = (e) => {
    const selected = e.target.files[0]
    if (selected) {
      setFile(selected)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    try {
      const result = await uploadSpedFile(file)
      // Armazenar resultado e navegar para o dashboard
      sessionStorage.setItem('analysisResult', JSON.stringify(result))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto' }}>
      {/* Hero */}
      <div className="text-center mb-6">
        <h2 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', marginBottom: 'var(--space-2)' }}>
          🛡️ Validação Expert
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-md)' }}>
          Envie o arquivo SPED EFD ICMS/IPI validado no PVA para análise técnica profunda.
        </p>
      </div>

      {/* Upload Zone */}
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt"
          onChange={handleSelect}
          style={{ display: 'none' }}
          id="sped-file-input"
        />

        {file ? (
          <>
            <span className="upload-icon">✅</span>
            <div>
              <div style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-md)' }}>
                {file.name}
              </div>
              <div style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
                {formatFileSize(file.size)}
              </div>
            </div>
            <button
              className="btn btn-secondary"
              onClick={(e) => { e.stopPropagation(); setFile(null) }}
              style={{ marginTop: 'var(--space-2)' }}
            >
              Trocar Arquivo
            </button>
          </>
        ) : (
          <>
            <span className="upload-icon">📂</span>
            <div className="upload-text">
              Arraste o arquivo <strong>.txt</strong> do SPED aqui
            </div>
            <div style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
              ou clique para selecionar
            </div>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="card mt-4" style={{ borderLeft: '4px solid var(--color-text-error)' }}>
          <div className="card-body" style={{ color: 'var(--color-text-error)' }}>
            ❌ {error}
          </div>
        </div>
      )}

      {/* Action */}
      {file && (
        <div className="text-center mt-6">
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={loading}
            id="btn-analyze"
            style={{ padding: 'var(--space-4) var(--space-8)', fontSize: 'var(--font-size-md)' }}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }}></span>
                Analisando...
              </>
            ) : (
              <>🔍 Analisar Arquivo</>
            )}
          </button>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="card mt-4">
          <div className="card-body">
            <div className="progress-bar" style={{ marginBottom: 'var(--space-3)' }}>
              <div
                className="progress-fill"
                style={{
                  width: `${Math.min(progress, 98)}%`,
                  background: 'var(--color-bg-accent)',
                  transition: 'width 0.5s ease-out',
                }}
              />
            </div>
            <p className="text-center" style={{ color: 'var(--color-text-secondary)' }}>
              Processando arquivo SPED... Aplicando validações matemáticas, cruzamentos e regras da UF.
            </p>
          </div>
        </div>
      )}

      {/* Info Cards */}
      <div className="stats-grid mt-6">
        <div className="card">
          <div className="card-body">
            <div style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--space-2)' }}>🧮</div>
            <h4 style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>Validação Matemática</h4>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
              Fórmulas do E110, G110, G125, E210 e E520 são verificadas automaticamente.
            </p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <div style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--space-2)' }}>🔗</div>
            <h4 style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>Cruzamento de Blocos</h4>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
              C190×E110, E111×E110, G125×G110, H010×0200 e mais.
            </p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <div style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--space-2)' }}>📜</div>
            <h4 style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>Regras por UF</h4>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
              Tabela 5.1.1, DIFAL, CIAP, obrigatoriedade de Bloco K e H.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadPage
