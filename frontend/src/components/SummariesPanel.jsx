import { useEffect, useRef, useState } from 'react'
import '../styles/components/SummariesPanel.css'
import SummaryResult from './SummaryResult'

function SummariesPanel({ summaries, summarizingId, expandedSummaryId, onExpandHandled }) {
  const [openIds, setOpenIds] = useState([])
  const sectionRefs = useRef({})

  useEffect(() => {
    if (!expandedSummaryId) return
    setOpenIds((current) =>
      current.includes(expandedSummaryId) ? current : [...current, expandedSummaryId],
    )
    sectionRefs.current[expandedSummaryId]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    onExpandHandled()
  }, [expandedSummaryId, onExpandHandled])

  function handleToggle(documentId, isOpen) {
    setOpenIds((current) =>
      isOpen
        ? current.includes(documentId)
          ? current
          : [...current, documentId]
        : current.filter((id) => id !== documentId),
    )
  }

  return (
    <section className="summaries-column">
      {summaries.map((entry) => (
        <details
          className="summary-section"
          key={entry.documentId}
          open={openIds.includes(entry.documentId)}
          onToggle={(event) => handleToggle(entry.documentId, event.currentTarget.open)}
          ref={(node) => {
            sectionRefs.current[entry.documentId] = node
          }}
        >
          <summary>Summary — {entry.source}</summary>
          <SummaryResult result={entry} />
        </details>
      ))}
      {summarizingId && (
        <div className="summary-section pending">
          <p className="muted">Summarizing…</p>
        </div>
      )}
    </section>
  )
}

export default SummariesPanel
