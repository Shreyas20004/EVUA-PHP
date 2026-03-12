export default function JobProgress({ status, totalFiles, completed, failed }) {
  const pct =
    totalFiles > 0
      ? Math.round(((completed + failed) / totalFiles) * 100)
      : 0

  const statusColors = {
    idle: 'var(--color-text-muted)',
    pending: 'var(--color-warning)',
    running: 'var(--color-info)',
    completed: 'var(--color-success)',
    failed: 'var(--color-danger)',
  }

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontWeight: 600 }}>
          Migration{' '}
          <span
            className={`badge badge-${status}`}
            style={{ color: statusColors[status] || 'inherit' }}
          >
            {status}
          </span>
        </span>
        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
          {completed + failed} / {totalFiles} files
        </span>
      </div>
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      {failed > 0 && (
        <p style={{ color: 'var(--color-danger)', marginTop: 8, fontSize: '0.8rem' }}>
          {failed} file(s) failed
        </p>
      )}
    </div>
  )
}
