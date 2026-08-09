import '../styles/components/AskPanel.css'

function AskPanel({
  question,
  onQuestionChange,
  answerMode,
  onAnswerModeChange,
  topK,
  onTopKChange,
  loading,
  onSubmit,
}) {
  return (
    <section className="card">
      <div className="card-heading">
        <h2>Ask</h2>
      </div>

      <form className="query-form" onSubmit={onSubmit}>
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          rows="3"
          placeholder="Ask about methods, results, limitations, or contributions."
        />
        <div className="control-row">
          <label>
            Mode
            <select value={answerMode} onChange={(event) => onAnswerModeChange(event.target.value)}>
              <option value="extractive">Extractive</option>
              <option value="openai">OpenAI</option>
            </select>
          </label>
          <label>
            Top K
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={(event) => onTopKChange(event.target.value)}
            />
          </label>
          <button type="submit" disabled={loading.query}>
            {loading.query ? 'Asking…' : 'Ask'}
          </button>
        </div>
      </form>
    </section>
  )
}

export default AskPanel
