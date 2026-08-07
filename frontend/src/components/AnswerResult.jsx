import EvidenceList from './EvidenceList'

function AnswerResult({ result, loading }) {
  if (!result) {
    return <p className="muted">{loading ? 'Asking…' : 'No answer yet.'}</p>
  }

  return (
    <>
      <p className="answer-text">{result.answer}</p>
      <details className="evidence-toggle">
        <summary>Evidence ({result.evidence.length})</summary>
        <EvidenceList evidence={result.evidence} />
      </details>
    </>
  )
}

export default AnswerResult
