import '../styles/components/SummaryResult.css'
import EvidenceList from './EvidenceList'
import { SUMMARY_FIELD_LABELS } from '../constants'

function SummaryResult({ result, loading }) {
  if (!result) {
    return <p className="muted">{loading ? 'Summarizing…' : 'Generate a summary to see the five-part paper brief.'}</p>
  }

  return (
    <div className="summary-list">
      {Object.entries(result.summary).map(([field, payload]) => (
        <details className="summary-item" key={field}>
          <summary>
            <span className="summary-label">{SUMMARY_FIELD_LABELS[field] || field.replaceAll('_', ' ')}</span>
          </summary>
          <div className="summary-body">
            <p>{payload.answer}</p>
            <details className="evidence-toggle">
              <summary>Evidence ({payload.evidence.length})</summary>
              <EvidenceList evidence={payload.evidence} />
            </details>
          </div>
        </details>
      ))}
    </div>
  )
}

export default SummaryResult
