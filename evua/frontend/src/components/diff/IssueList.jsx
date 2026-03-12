/**
 * Renders a list of migration issues.
 */
const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info']

export default function IssueList({ issues = [] }) {
  if (!issues.length) {
    return (
      <p style={{ color: 'var(--color-text-muted)', padding: '8px 0' }}>
        No issues found.
      </p>
    )
  }

  const sorted = [...issues].sort(
    (a, b) =>
      SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
  )

  return (
    <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
      {sorted.map((issue, i) => (
        <li
          key={i}
          style={{
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
            borderRadius: 6,
            padding: '10px 14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span className={`badge badge-${issue.severity}`}>
              {issue.severity.toUpperCase()}
            </span>
            <code style={{ fontSize: '0.75rem', color: 'var(--color-primary)' }}>
              {issue.rule_id}
            </code>
            <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
              line {issue.line}
            </span>
          </div>
          <p style={{ fontSize: '0.85rem' }}>{issue.message}</p>
          {issue.original_code && (
            <code
              style={{
                display: 'block',
                marginTop: 6,
                fontSize: '0.78rem',
                color: '#fca5a5',
                background: 'rgba(239,68,68,0.08)',
                padding: '4px 8px',
                borderRadius: 4,
              }}
            >
              {issue.original_code}
            </code>
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
            {issue.auto_fixable && (
              <span style={{ fontSize: '0.72rem', color: 'var(--color-success)' }}>
                ✓ auto-fixable
              </span>
            )}
            {issue.requires_ai && (
              <span style={{ fontSize: '0.72rem', color: 'var(--color-warning)' }}>
                ✦ requires AI
              </span>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}
