import AnswerResult from './AnswerResult'
import SummaryResult from './SummaryResult'

function ResultsPanel({ resultView, queryResult, summaryResult, loading }) {
  if (!resultView) return null

  return (
    <section className="results-column">
      <div className="card">
        <div className="card-heading">
          <h2>{resultView === 'summary' ? 'Summary' : 'Answer'}</h2>
        </div>
        {resultView === 'summary' ? (
          <SummaryResult result={summaryResult} loading={loading.summary} />
        ) : (
          <AnswerResult result={queryResult} loading={loading.query} />
        )}
      </div>
    </section>
  )
}

export default ResultsPanel
