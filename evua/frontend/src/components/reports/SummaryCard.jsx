/**
 * Summary card showing migration statistics.
 */
export default function SummaryCard({ summary = {}, totalFiles = 0, completed = 0, failed = 0, skipped = 0 }) {
  const stats = [
    { label: 'Total files',       value: totalFiles,                          color: 'var(--color-text)' },
    { label: 'Completed',         value: completed,                           color: 'var(--color-success)' },
    { label: 'Failed',            value: failed,                              color: 'var(--color-danger)' },
    { label: 'Skipped',           value: skipped,                             color: 'var(--color-text-muted)' },
    { label: 'Total issues',      value: summary.total_issues ?? '—',         color: 'var(--color-warning)' },
    { label: 'Auto-fixes applied', value: summary.rule_fixes_applied ?? '—',  color: 'var(--color-primary)' },
    { label: 'AI fixes applied',  value: summary.ai_fixes_applied ?? '—',     color: 'var(--color-info)' },
  ]

  return (
    <div className="card">
      <h3 style={{ marginBottom: 16 }}>Migration Summary</h3>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
          gap: 12,
        }}
      >
        {stats.map(({ label, value, color }) => (
          <div
            key={label}
            style={{
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
              borderRadius: 6,
              padding: '12px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
              {label}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
