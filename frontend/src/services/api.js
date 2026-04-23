const API_BASE = '/api'

export async function uploadSpedFile(file, obrigacao = 'efd') {
  const formData = new FormData()
  formData.append('files', file) // Backend (FastAPI) espera a chave 'files'

  const response = await fetch(`${API_BASE}/upload?obrigacao=${obrigacao}`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    let errorMsg = 'Erro ao processar o arquivo.'
    if (error.detail) {
      if (Array.isArray(error.detail)) {
        // Formata erro de validação do FastAPI
        errorMsg = error.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      } else if (typeof error.detail === 'string') {
        errorMsg = error.detail
      } else {
        errorMsg = JSON.stringify(error.detail)
      }
    }
    throw new Error(errorMsg)
  }

  return response.json()
}

export async function uploadMultipleFiles(files) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }

  const response = await fetch(`${API_BASE}/upload/compare`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    let errorMsg = 'Erro ao processar os arquivos.'
    if (error.detail) {
      if (Array.isArray(error.detail)) {
        errorMsg = error.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
      } else if (typeof error.detail === 'string') {
        errorMsg = error.detail
      } else {
        errorMsg = JSON.stringify(error.detail)
      }
    }
    throw new Error(errorMsg)
  }

  return response.json()
}

export async function exportReport(analysisId, format, fileName = null) {
  const response = await fetch(`${API_BASE}/export/${analysisId}/${format}`)
  if (!response.ok) {
    let errorMsg = 'Erro ao gerar relatório.'
    try {
      const errData = await response.json()
      errorMsg = errData.detail || errorMsg
    } catch(e) {}
    throw new Error(errorMsg)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName ? `${fileName}.${format}` : `dossie_${analysisId.slice(0, 8)}.${format}`
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  a.remove()
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE.replace('/api', '')}/health`)
  return response.json()
}
