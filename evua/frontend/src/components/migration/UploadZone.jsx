import { useCallback, useRef, useState } from 'react'

export default function UploadZone({ onFiles }) {
  const [dragging, setDragging] = useState(false)
  const [fileList, setFileList] = useState([])
  const inputRef = useRef()

  const handleFiles = useCallback(
    (files) => {
      const arr = Array.from(files).filter(
        (f) => f.name.endsWith('.php') || f.name.endsWith('.phtml') || f.name.endsWith('.zip')
      )
      setFileList(arr)
      onFiles(arr)
    },
    [onFiles]
  )

  return (
    <div>
      <div
        className={`upload-zone${dragging ? ' drag-over' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          handleFiles(e.dataTransfer.files)
        }}
      >
        <div className="upload-icon">📂</div>
        <p style={{ color: 'var(--color-text)' }}>
          Drag PHP files or a ZIP archive here, or <strong>click to browse</strong>
        </p>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', marginTop: 4 }}>
          Accepts .php / .phtml / .zip
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".php,.phtml,.zip"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {fileList.length > 0 && (
        <ul style={{ marginTop: 12, listStyle: 'none', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {fileList.map((f) => (
            <li
              key={f.name}
              style={{
                background: 'var(--color-border)',
                padding: '4px 10px',
                borderRadius: 6,
                fontSize: '0.8rem',
                color: 'var(--color-text)',
              }}
            >
              {f.name.endsWith('.zip') ? '🗜️' : '📄'} {f.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
