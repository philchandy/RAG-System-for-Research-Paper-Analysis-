import '../styles/components/EvidenceList.css'

function EvidenceList({ evidence = [] }) {
  if (!evidence.length) {
    return <p className="muted">No evidence chunks returned.</p>
  }

  return (
    <div className="evidence-list">
      {evidence.map((item, index) => (
        <article className="evidence-card" key={`${item.chunk_id}-${index}`}>
          <div className="evidence-meta">
            <span>{item.source || 'Unknown source'}</span>
            <span>{item.section || 'Unknown section'}</span>
          </div>
          <p>{item.text}</p>
        </article>
      ))}
    </div>
  )
}

export default EvidenceList
