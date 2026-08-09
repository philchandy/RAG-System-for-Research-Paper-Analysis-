import '../styles/components/ResultsPanel.css'
import AnswerResult from './AnswerResult'

function ResultsPanel({ queryResult, loading }) {
  return (
    <section className="results-column">
      <div className="card">
        <div className="card-heading">
          <h2>Answer</h2>
        </div>
        <AnswerResult result={queryResult} loading={loading.query} />
      </div>
    </section>
  )
}

export default ResultsPanel
