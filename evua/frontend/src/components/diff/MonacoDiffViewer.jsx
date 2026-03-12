import { useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'

/**
 * Monaco-based diff viewer for PHP migration code
 * Shows original vs migrated code side-by-side with syntax highlighting
 */
export default function MonacoDiffViewer({
  original,
  migrated,
  filePath,
  language = 'php',
}) {
  const [editorTheme, setEditorTheme] = useState('vs-light')

  // Detect system dark mode preference
  useEffect(() => {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setEditorTheme(isDark ? 'vs-dark' : 'vs-light')
  }, [])

  if (!original || !migrated) {
    return (
      <div style={{
        padding: '16px',
        color: 'var(--color-text-muted)',
        fontSize: '0.875rem',
      }}>
        No code to display
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header with file info */}
      {filePath && (
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--color-border)',
          fontSize: '0.8rem',
          color: 'var(--color-text-muted)',
          background: 'var(--color-bg)',
        }}>
          {filePath}
        </div>
      )}

      {/* Side-by-side editors */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* Original code */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid var(--color-border)',
        }}>
          <div style={{
            padding: '8px 12px',
            background: 'rgba(239,68,68,0.05)',
            borderBottom: '1px solid var(--color-border)',
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--color-danger)',
          }}>
            Original Code
          </div>
          <Editor
            height="100%"
            language={language}
            theme={editorTheme}
            value={original}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              wordWrap: 'on',
              fontSize: 12,
              fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", monospace',
              contextmenu: false,
            }}
          />
        </div>

        {/* Migrated code */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{
            padding: '8px 12px',
            background: 'rgba(34,197,94,0.05)',
            borderBottom: '1px solid var(--color-border)',
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--color-success)',
          }}>
            Migrated Code
          </div>
          <Editor
            height="100%"
            language={language}
            theme={editorTheme}
            value={migrated}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              wordWrap: 'on',
              fontSize: 12,
              fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", monospace',
              contextmenu: false,
            }}
          />
        </div>
      </div>

      {/* Code statistics footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--color-border)',
        background: 'var(--color-bg)',
        fontSize: '0.75rem',
        color: 'var(--color-text-muted)',
        display: 'flex',
        gap: '20px',
      }}>
        <span>Original: {original?.split('\n').length || 0} lines, {original?.length || 0} bytes</span>
        <span>Migrated: {migrated?.split('\n').length || 0} lines, {migrated?.length || 0} bytes</span>
      </div>
    </div>
  )
}
