import { useEffect, useState } from 'react'
import {
  checkHealth,
  deleteDocument,
  listDocuments,
  queryDocuments,
  summarizeDocuments,
  uploadDocument,
} from '../api'
import { DEFAULT_QUESTION } from '../constants'

// Owns all app state and API orchestration so components stay presentational.
export function usePaperAssistant() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [documents, setDocuments] = useState([])
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([])
  const [question, setQuestion] = useState(DEFAULT_QUESTION)
  const [topK, setTopK] = useState(3)
  const [answerMode, setAnswerMode] = useState('extractive')
  const [selectedFile, setSelectedFile] = useState(null)
  const [queryResult, setQueryResult] = useState(null)
  const [summaryResult, setSummaryResult] = useState(null)
  const [resultView, setResultView] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState({
    documents: false,
    upload: false,
    query: false,
    summary: false,
    deleteId: null,
  })

  async function refreshDocuments() {
    setLoading((current) => ({ ...current, documents: true }))
    try {
      const payload = await listDocuments()
      setDocuments(payload.documents)
      setSelectedDocumentIds((current) =>
        current.filter((documentId) =>
          payload.documents.some((document) => document.document_id === documentId),
        ),
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((current) => ({ ...current, documents: false }))
    }
  }

  useEffect(() => {
    async function boot() {
      try {
        await checkHealth()
        setBackendStatus('online')
      } catch (err) {
        setBackendStatus('offline')
        setError(err.message)
      }

      refreshDocuments()
    }

    boot()
  }, [])

  function toggleDocument(documentId) {
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    )
  }

  function makeRequestPayload() {
    return {
      document_ids: selectedDocumentIds.length ? selectedDocumentIds : null,
      top_k: Number(topK),
      answer_mode: answerMode,
    }
  }

  async function handleUpload(event) {
    event.preventDefault()
    if (!selectedFile) {
      setError('Choose a PDF before uploading.')
      return
    }

    setError('')
    setMessage('Indexing PDF. This can take a moment.')
    setLoading((current) => ({ ...current, upload: true }))

    try {
      const payload = await uploadDocument(selectedFile)
      setMessage(`Indexed ${payload.report.source} with ${payload.report.chunk_count} chunks.`)
      setSelectedFile(null)
      await refreshDocuments()
      setSelectedDocumentIds((current) => [...new Set([...current, payload.report.document_id])])
    } catch (err) {
      setError(err.message)
      setMessage('')
    } finally {
      setLoading((current) => ({ ...current, upload: false }))
    }
  }

  async function handleQuery(event) {
    event.preventDefault()
    if (!question.trim()) {
      setError('Enter a question before querying.')
      return
    }

    setError('')
    setMessage('')
    setResultView('answer')
    setLoading((current) => ({ ...current, query: true }))

    try {
      const payload = await queryDocuments({
        ...makeRequestPayload(),
        question: question.trim(),
      })
      setQueryResult(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((current) => ({ ...current, query: false }))
    }
  }

  async function handleSummarize() {
    setError('')
    setMessage('')
    setResultView('summary')
    setLoading((current) => ({ ...current, summary: true }))

    try {
      const payload = await summarizeDocuments(makeRequestPayload())
      setSummaryResult(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((current) => ({ ...current, summary: false }))
    }
  }

  async function handleDelete(documentId) {
    setError('')
    setMessage('')
    setLoading((current) => ({ ...current, deleteId: documentId }))

    try {
      const payload = await deleteDocument(documentId)
      setMessage(`Deleted ${payload.source || payload.document_id}.`)
      setQueryResult(null)
      setSummaryResult(null)
      setResultView(null)
      await refreshDocuments()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((current) => ({ ...current, deleteId: null }))
    }
  }

  return {
    backendStatus,
    documents,
    selectedDocumentIds,
    question,
    setQuestion,
    topK,
    setTopK,
    answerMode,
    setAnswerMode,
    selectedFile,
    setSelectedFile,
    queryResult,
    summaryResult,
    resultView,
    message,
    error,
    loading,
    refreshDocuments,
    toggleDocument,
    handleUpload,
    handleQuery,
    handleSummarize,
    handleDelete,
  }
}
