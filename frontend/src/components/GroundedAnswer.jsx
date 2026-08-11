import { useEffect, useRef, useState } from 'react'
import '../styles/components/GroundedAnswer.css'
import EvidenceList from './EvidenceList'

const CITATION_RE = /\[([^[\]]+)\]/g

// Splits "intro: 1. foo 2. bar" style run-on enumerations into list items.
// Only fires when the numbering starts at 1 and increments, to avoid
// splitting on things like "Table 4." inside quoted evidence.
function splitInlineEnumeration(text) {
  const parts = text.replace(/([\s:;])(\d+[.)]\s)/g, '$1\u0000$2').split('\u0000')
  if (parts.length < 2) return null

  let intro = ''
  const items = []
  const numbers = []

  for (const part of parts) {
    const match = part.trim().match(/^(\d+)[.)]\s+(.*)$/s)
    if (match) {
      numbers.push(Number(match[1]))
      items.push(match[2].trim())
    } else if (!items.length) {
      intro += part
    } else {
      items[items.length - 1] += ` ${part.trim()}`
    }
  }

  const sequential = numbers.length >= 2 && numbers.every((n, i) => n === i + 1)
  if (!sequential) return null

  return { intro: intro.trim(), items }
}

function parseBlocks(text) {
  const blocks = []
  let list = null
  let paragraph = []
  let listHasBlankLine = false

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push({ type: 'p', text: paragraph.join(' ') })
      paragraph = []
    }
  }
  const flushList = () => {
    if (list) {
      blocks.push(list)
      list = null
    }
  }

  for (const rawLine of String(text).split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line) {
      flushParagraph()
      if (list) listHasBlankLine = true
      continue
    }

    const ordered = line.match(/^\d+[.)]\s+(.*)$/)
    const unordered = line.match(/^[-•*]\s+(.*)$/)

    if (ordered || unordered) {
      flushParagraph()
      const type = ordered ? 'ol' : 'ul'
      if (!list || list.type !== type) {
        flushList()
        list = { type, items: [] }
      }
      list.items.push(ordered ? ordered[1] : unordered[1])
      listHasBlankLine = false
    } else if (list && !listHasBlankLine) {
      list.items[list.items.length - 1] += ` ${line}`
    } else {
      flushList()
      listHasBlankLine = false
      paragraph.push(line)
    }
  }
  flushParagraph()
  flushList()

  // Break up single-paragraph enumerations ("1. ... 2. ...") into real lists.
  const expanded = []
  for (const block of blocks) {
    if (block.type !== 'p') {
      expanded.push(block)
      continue
    }
    const enumeration = splitInlineEnumeration(block.text)
    if (enumeration) {
      if (enumeration.intro) expanded.push({ type: 'p', text: enumeration.intro })
      expanded.push({ type: 'ol', items: enumeration.items })
    } else {
      expanded.push(block)
    }
  }

  return expanded
}

function renderInline(text, chunkIds, onCitationClick) {
  const nodes = []
  let cursor = 0

  for (const match of text.matchAll(CITATION_RE)) {
    const [full, id] = match
    if (match.index > cursor) nodes.push(text.slice(cursor, match.index))

    if (chunkIds.has(id)) {
      nodes.push(
        <button
          type="button"
          className="citation"
          key={`${id}-${match.index}`}
          title="Jump to evidence"
          onClick={() => onCitationClick(id)}
        >
          [{id}]
        </button>,
      )
    } else {
      nodes.push(full)
    }
    cursor = match.index + full.length
  }

  if (cursor < text.length) nodes.push(text.slice(cursor))
  return nodes
}

function GroundedAnswer({ text, evidence = [] }) {
  const containerRef = useRef(null)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [pendingChunkId, setPendingChunkId] = useState(null)

  const chunkIds = new Set(evidence.map((item) => String(item.chunk_id)))

  useEffect(() => {
    if (!pendingChunkId) return
    const card = containerRef.current?.querySelector(
      `[data-chunk-id="${CSS.escape(pendingChunkId)}"]`,
    )
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' })
      card.classList.add('flash')
      setTimeout(() => card.classList.remove('flash'), 1500)
    }
    setPendingChunkId(null)
  }, [pendingChunkId])

  function jumpToChunk(chunkId) {
    setEvidenceOpen(true)
    setPendingChunkId(chunkId)
  }

  const blocks = parseBlocks(text)

  return (
    <div className="grounded-answer" ref={containerRef}>
      <div className="answer-text">
        {blocks.map((block, index) =>
          block.type === 'p' ? (
            <p key={index}>{renderInline(block.text, chunkIds, jumpToChunk)}</p>
          ) : block.type === 'ol' ? (
            <ol key={index}>
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInline(item, chunkIds, jumpToChunk)}</li>
              ))}
            </ol>
          ) : (
            <ul key={index}>
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInline(item, chunkIds, jumpToChunk)}</li>
              ))}
            </ul>
          ),
        )}
      </div>
      <details
        className="evidence-toggle"
        open={evidenceOpen}
        onToggle={(event) => setEvidenceOpen(event.currentTarget.open)}
      >
        <summary>Evidence ({evidence.length})</summary>
        <EvidenceList evidence={evidence} />
      </details>
    </div>
  )
}

export default GroundedAnswer
