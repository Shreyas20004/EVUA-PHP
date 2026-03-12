import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHealth, listJobs } from '../services/api.js'

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    getHealth()
      .then((r) => setHealth(r.data))
      .catch(() => setHealth({ status: 'unreachable' }))
    listJobs()
      .then((data) => setJobs(data))
      .catch(() => {})
  }, [])

  return (
    <div style={{ maxWidth: 860 }}>
      <h1 style={{ marginBottom: 24 }}>Dashboard</h1>

      {/* Backend health */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h2 style={{ marginBottom: 12 }}>Backend Status</h2>
        {health ? (
          <p>
            Status:{' '}
            <span
              style={{
                color: health.status === 'ok' ? 'var(--color-success)' : 'var(--color-danger)',
                fontWeight: 600,
              }}
            >
              {health.status}
            </span>
            {health.python && (
              <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', marginLeft: 12 }}>
                Python {health.python.split(' ')[0]}
              </span>
            )}
          </p>
        ) : (
          <p style={{ color: 'var(--color-text-muted)' }}>Connecting…</p>
        )}
      </div>

      {/* Quick-start */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h2 style={{ marginBottom: 12 }}>Quick Start</h2>
        <p style={{ color: 'var(--color-text-muted)', marginBottom: 16 }}>
          Upload your PHP files and migrate them to a newer version in minutes.
        </p>
        <Link to="/migrate" className="btn btn-primary">
          Start Migration →
        </Link>
      </div>

      {/* Recent jobs */}
      <div className="card">
        <h2 style={{ marginBottom: 12 }}>Recent Jobs</h2>
        {jobs.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)' }}>No jobs yet.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['Job ID', 'Status', 'Actions'].map((h) => (
                  <th key={h} style={{ textAlign: 'left', padding: '8px 0', color: 'var(--color-text-muted)', fontWeight: 500 }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.job_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '10px 0', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {j.job_id.slice(0, 8)}…
                  </td>
                  <td style={{ padding: '10px 0' }}>
                    <span className={`badge badge-${j.status}`}>{j.status}</span>
                  </td>
                  <td style={{ padding: '10px 0' }}>
                    <Link to={`/results/${j.job_id}`} style={{ fontSize: '0.85rem' }}>
                      View results →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
