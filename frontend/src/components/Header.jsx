function Header({ backendStatus }) {
  return (
    <header className="app-header">
      <p className="brand">Paper Assistant</p>
      <div className={`status-pill ${backendStatus}`}>
        <span aria-hidden="true"></span>
        {backendStatus}
      </div>
    </header>
  )
}

export default Header
