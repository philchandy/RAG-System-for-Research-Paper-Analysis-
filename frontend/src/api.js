const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const payload = await response.json()
      message = payload.detail || message
    } catch {
      // Keep the generic status message when the backend returns no JSON body.
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export function checkHealth() {
  return request('/health')
}

export function listDocuments() {
  return request('/documents')
}

export function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  return request('/documents', {
    method: 'POST',
    body: formData,
  })
}

export function deleteDocument(documentId) {
  return request(`/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
  })
}

export function queryDocuments(payload) {
  return request('/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function summarizeDocuments(payload) {
  return request('/summarize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

