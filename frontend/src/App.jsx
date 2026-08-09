import './styles/App.css'
import Header from './components/Header'
import Notice from './components/Notice'
import LibraryPanel from './components/LibraryPanel'
import AskPanel from './components/AskPanel'
import ResultsPanel from './components/ResultsPanel'
import SummariesPanel from './components/SummariesPanel'
import { usePaperAssistant } from './hooks/usePaperAssistant'

function App() {
  const {
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
    summaries,
    expandedSummaryId,
    setExpandedSummaryId,
    message,
    error,
    loading,
    refreshDocuments,
    toggleDocument,
    handleUpload,
    handleQuery,
    handleSummarize,
    handleDelete,
  } = usePaperAssistant()

  const hasAnswer = Boolean(queryResult) || loading.query
  const hasSummaries = summaries.length > 0 || Boolean(loading.summarizeId)

  return (
    <main className="app-shell">
      <Header />
      <Notice error={error} message={message} />

      <div
        className={`layout ${hasAnswer ? 'has-answer' : ''} ${hasSummaries ? 'has-summaries' : ''}`}
      >
        <section className="agent-column">
          <LibraryPanel
            documents={documents}
            selectedDocumentIds={selectedDocumentIds}
            summarizedIds={summaries.map((entry) => entry.documentId)}
            selectedFile={selectedFile}
            loading={loading}
            onRefresh={refreshDocuments}
            onUpload={handleUpload}
            onFileChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
            onToggleDocument={toggleDocument}
            onSummarize={handleSummarize}
            onDelete={handleDelete}
          />

          <AskPanel
            question={question}
            onQuestionChange={setQuestion}
            answerMode={answerMode}
            onAnswerModeChange={setAnswerMode}
            topK={topK}
            onTopKChange={setTopK}
            loading={loading}
            onSubmit={handleQuery}
          />
        </section>

        {hasAnswer && <ResultsPanel queryResult={queryResult} loading={loading} />}

        {hasSummaries && (
          <SummariesPanel
            summaries={summaries}
            summarizingId={loading.summarizeId}
            expandedSummaryId={expandedSummaryId}
            onExpandHandled={() => setExpandedSummaryId(null)}
          />
        )}
      </div>
    </main>
  )
}

export default App

