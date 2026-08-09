import '../styles/components/AnswerResult.css'
import GroundedAnswer from './GroundedAnswer'

function AnswerResult({ result, loading }) {
  if (!result) {
    return <p className="muted">{loading ? 'Asking…' : 'No answer yet.'}</p>
  }

  return (
    <GroundedAnswer text={result.answer} evidence={result.evidence} />
  )
}

export default AnswerResult
