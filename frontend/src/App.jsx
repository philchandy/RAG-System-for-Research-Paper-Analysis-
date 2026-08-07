import './App.css'
import Header from './components/Header'
import Notice from './components/Notice'
import LibraryPanel from './components/LibraryPanel'
import AskPanel from './components/AskPanel'
import ResultsPanel from './components/ResultsPanel'
import { usePaperAssistant } from './hooks/usePaperAssistant'

function App() {
  const {
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
  } = usePaperAssistant()

  return (
    <main className="app-shell">
      <Header backendStatus={backendStatus} />
      <Notice error={error} message={message} />

      <div className={`layout ${resultView ? 'has-results' : ''}`}>
        <section className="agent-column">
          <LibraryPanel
            documents={documents}
            selectedDocumentIds={selectedDocumentIds}
            selectedFile={selectedFile}
            loading={loading}
            onRefresh={refreshDocuments}
            onUpload={handleUpload}
            onFileChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
            onToggleDocument={toggleDocument}
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
            onSummarize={handleSummarize}
          />
        </section>

        <ResultsPanel
          resultView={resultView}
          queryResult={queryResult}
          summaryResult={summaryResult}
          loading={loading}
        />
      </div>
    </main>
  )
}

export default App

