/**
 * Renders a unified diff string as styled HTML.
 */
export default function DiffViewer({ diff, filePath }) {
  if (!diff) {
    return (
      <p style={{ color: 'var(--color-text-muted)', padding: '16px 0' }}>
        No changes.
      </p>
    )
  }

  const lines = diff.split('\n')

  return (
    <div>
      {filePath && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 8 }}>
          {filePath}
        </p>
      )}
      <pre className="evua-diff">
        {lines.map((line, i) => {
          let cls = 'diff-ctx'
          if (line.startsWith('+++') || line.startsWith('---')) cls = 'diff-meta'
          else if (line.startsWith('+')) cls = 'diff-add'
          else if (line.startsWith('-')) cls = 'diff-del'
          else if (line.startsWith('@@')) cls = 'diff-hunk'
          return (
            <span key={i} className={cls}>
              {line}
            </span>
          )
        })}
      </pre>
    </div>
  )
}
