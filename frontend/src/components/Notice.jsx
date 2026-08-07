function Notice({ error, message }) {
  if (!error && !message) return null

  return <p className={`notice ${error ? 'error' : 'success'}`}>{error || message}</p>
}

export default Notice
