import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { uploadSpedFile } from '../services/api'

function UploadPage() {
  const { obrigacao } = useParams()
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()
  const navigate = useNavigate()

  // Configuração Dinâmica por Obrigação
  const config = {
    efd: {
      title: "Validação Expert EFD",
      subtitle: "Envie o arquivo SPED EFD ICMS/IPI validado no PVA para análise técnica profunda.",
      placeholderText: "Arraste o arquivo .txt do SPED aqui",
      loadingText: "Processando arquivo SPED... Aplicando validações matemáticas, cruzamentos e regras da UF.",
      themeColor: "var(--color-primary)",
      cards: [
        { icon: "🧮", title: "Validação Matemática", desc: "Fórmulas do E110, G110, G125, E210 e E520 verificadas automaticamente." },
        { icon: "🔗", title: "Cruzamento de Blocos", desc: "C190×E110, E111×E110, G125×G110, H010×0200 e mais." },
        { icon: "📜", title: "Regras por UF", desc: "Tabela 5.1.1, DIFAL, CIAP, obrigatoriedade de Bloco K e H." }
      ]
    },
    ecd: {
      title: "Auditoria Contábil ECD",
      subtitle: "Envie o arquivo da Escrituração Contábil Digital para auditoria das partidas dobradas.",
      placeholderText: "Arraste o arquivo .txt da ECD aqui",
      loadingText: "Processando arquivo ECD... Validando balancetes, lançamentos e método das partidas dobradas.",
      themeColor: "#059669",
      cards: [
        { icon: "⚖️", title: "Partidas Dobradas", desc: "Validação matemática rigorosa entre Débitos e Créditos (I200, I250)." },
        { icon: "📊", title: "Saldos e Balancetes", desc: "Auditoria de saldos anteriores e atuais nos registros I150 e I155." },
        { icon: "📑", title: "Plano de Contas", desc: "Análise da consistência do plano de contas e centros de custos." }
      ]
    },
    ecf: {
      title: "Compliance Fiscal ECF",
      subtitle: "Envie o arquivo da ECF validado no PVA para cruzamentos de IRPJ, CSLL e blocos M.",
      placeholderText: "Arraste o arquivo .txt da ECF aqui",
      loadingText: "Processando arquivo ECF... Aplicando cruzamentos avançados LALUR e LACS.",
      themeColor: "#6C5CE7",
      cards: [
        { icon: "🏢", title: "IRPJ e CSLL", desc: "Cálculo e conciliação do lucro real, presumido ou arbitrado." },
        { icon: "📈", title: "Blocos M e N", desc: "Auditoria detalhada do e-LALUR e e-LACS (Parte A e Parte B)." },
        { icon: "🔗", title: "Recuperação ECD", desc: "Verificação da correta amarração com a contabilidade recuperada." }
      ]
    }
  }

  const currentConfig = config[obrigacao] || config.efd;

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
      setError('Formato inválido. Envie um arquivo .txt.')
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
      // Repassa a obrigação para a API
      const result = await uploadSpedFile(file, obrigacao)
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
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Hero */}
      <div className="text-center mb-6">
        <h2 style={{ 
          fontSize: 'var(--font-size-2xl)', 
          fontWeight: 'var(--font-weight-bold)', 
          marginBottom: 'var(--space-2)',
          color: currentConfig.themeColor 
        }}>
          🛡️ {currentConfig.title}
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-md)' }}>
          {currentConfig.subtitle}
        </p>
      </div>

      {/* Upload Zone */}
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && inputRef.current?.click()}
        style={dragging ? { borderColor: currentConfig.themeColor } : {}}
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
            <span className="upload-icon" style={{ color: currentConfig.themeColor }}>✅</span>
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
            <span className="upload-icon" style={{ color: currentConfig.themeColor }}>📂</span>
            <div className="upload-text">
              {currentConfig.placeholderText.split('.txt').map((part, i, arr) => 
                i === arr.length - 1 ? part : <span key={i}>{part}<strong>.txt</strong></span>
              )}
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
            style={{ 
              padding: 'var(--space-4) var(--space-8)', 
              fontSize: 'var(--font-size-md)',
              backgroundColor: currentConfig.themeColor,
              borderColor: currentConfig.themeColor 
            }}
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

      {/* Modal de Progresso */}
      {loading && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div className="card" style={{ 
            width: '500px', 
            maxWidth: '90%', 
            boxShadow: '0 10px 25px rgba(0,0,0,0.2)' 
          }}>
            <div className="card-body" style={{ padding: 'var(--space-8)' }}>
              <h3 style={{ textAlign: 'center', marginBottom: 'var(--space-6)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-lg)' }}>
                🔍 Analisando Arquivo...
              </h3>
              <div className="progress-bar" style={{ marginBottom: 'var(--space-4)', height: '8px' }}>
                <div
                  className="progress-fill"
                  style={{
                    width: `${Math.min(progress, 98)}%`,
                    background: currentConfig.themeColor,
                    transition: 'width 0.5s ease-out',
                  }}
                />
              </div>
              <p className="text-center" style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                {currentConfig.loadingText}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Cards */}
      <div className="stats-grid mt-6">
        {currentConfig.cards.map((card, index) => (
          <div className="card" key={index} style={{ borderTop: `3px solid ${currentConfig.themeColor}` }}>
            <div className="card-body">
              <div style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--space-2)' }}>{card.icon}</div>
              <h4 style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>{card.title}</h4>
              <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
                {card.desc}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default UploadPage
