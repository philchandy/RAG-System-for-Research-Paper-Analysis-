function LibraryPanel({
  documents,
  selectedDocumentIds,
  selectedFile,
  loading,
  onRefresh,
  onUpload,
  onFileChange,
  onToggleDocument,
  onDelete,
}) {
  return (
    <section className="card">
      <div className="card-heading">
        <h2>Library</h2>
        <button type="button" className="ghost-button" onClick={onRefresh} disabled={loading.documents}>
          {loading.documents ? 'Refreshing' : 'Refresh'}
        </button>
      </div>

      <form className="upload-box" onSubmit={onUpload}>
        <label className="dropzone" htmlFor="pdf-upload">
          <span>{selectedFile ? selectedFile.name : 'Choose a PDF to upload'}</span>
        </label>
        <input id="pdf-upload" type="file" accept="application/pdf" onChange={onFileChange} />
        <button type="submit" disabled={loading.upload || !selectedFile}>
          {loading.upload ? 'Indexing…' : 'Upload & index'}
        </button>
      </form>

      <div className="document-list">
        {documents.length === 0 && <p className="muted">No indexed documents yet.</p>}
        {documents.map((document) => (
          <article className="document-row" key={document.document_id}>
            <label>
              <input
                type="checkbox"
                checked={selectedDocumentIds.includes(document.document_id)}
                onChange={() => onToggleDocument(document.document_id)}
              />
              <span>
                <strong>{document.source || document.document_id}</strong>
                <small>{document.chunk_count} chunks</small>
              </span>
            </label>
            <button
              type="button"
              className="danger-button"
              onClick={() => onDelete(document.document_id)}
              disabled={loading.deleteId === document.document_id}
            >
              {loading.deleteId === document.document_id ? '…' : 'Remove'}
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}

export default LibraryPanel
