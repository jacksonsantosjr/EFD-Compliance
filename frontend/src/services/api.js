const API_BASE = '/api'

export async function uploadSpedFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erro ao processar o arquivo.')
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
    throw new Error(error.detail || 'Erro ao processar os arquivos.')
  }

  return response.json()
}

export async function exportReport(analysisId, format) {
  const response = await fetch(`${API_BASE}/export/${analysisId}/${format}`)
  if (!response.ok) throw new Error('Erro ao gerar relatório.')

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `dossie_${analysisId.slice(0, 8)}.${format}`
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  a.remove()
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE.replace('/api', '')}/health`)
  return response.json()
}
