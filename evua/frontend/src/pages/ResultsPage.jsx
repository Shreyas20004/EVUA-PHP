import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getJobStatus } from '../services/api.js'
import SummaryCard from '../components/reports/SummaryCard.jsx'
import MonacoDiffViewer from '../components/diff/MonacoDiffViewer.jsx'
import DiffViewer from '../components/diff/DiffViewer.jsx'
import IssueList from '../components/diff/IssueList.jsx'
import VersionHistoryPanel from '../components/version/VersionHistoryPanel.jsx'

export default function ResultsPage() {
  const { jobId } = useParams()
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedFile, setSelectedFile] = useState(null)
  const [activeTab, setActiveTab] = useState('diff')
  const [mainTab, setMainTab] = useState('files')

  useEffect(() => {
    setLoading(true)
    getJobStatus(jobId)
      .then((data) => {
        setJob(data)
        if (data.results?.length) setSelectedFile(data.results[0])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) return <p style={{ color: 'var(--color-text-muted)' }}>Loading results…</p>
  if (!job) return <p style={{ color: 'var(--color-danger)' }}>Job not found.</p>

  const fileResult = job.results?.find((r) => r.file_path === selectedFile?.file_path)

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <Link to="/dashboard" style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
          ← Dashboard
        </Link>
        <h1>Migration Results</h1>
        <span className={`badge badge-${job.status}`}>{job.status}</span>
      </div>

      <SummaryCard
        summary={job.summary}
        totalFiles={job.total_files}
        completed={job.completed}
        failed={job.failed}
        skipped={job.skipped}
      />

      {/* Top-level tabs: Files / History */}
      <div style={{ display: 'flex', gap: 0, marginTop: 20, borderBottom: '1px solid var(--color-border)' }}>
        {['files', 'history'].map((t) => (
          <button
            key={t}
            onClick={() => setMainTab(t)}
            style={{
              background: 'none', border: 'none',
              borderBottom: mainTab === t ? '2px solid var(--color-primary)' : '2px solid transparent',
              padding: '8px 20px', cursor: 'pointer',
              color: mainTab === t ? 'var(--color-primary)' : 'var(--color-text-muted)',
              fontWeight: mainTab === t ? 600 : 400,
              fontSize: '0.9rem', textTransform: 'capitalize',
            }}
          >
            {t === 'history' ? '↩ History' : '📄 Files'}
          </button>
        ))}
      </div>

      {mainTab === 'history' && (
        <div style={{ marginTop: 20 }}>
          <VersionHistoryPanel jobId={jobId} />
        </div>
      )}

      {mainTab === 'files' && job.results?.length > 0 && (
        <div style={{ display: 'flex', gap: 16, marginTop: 20 }}>
          {/* File list */}
          <div
            style={{
              width: 240,
              flexShrink: 0,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius)',
              overflow: 'hidden',
            }}
          >
            <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--color-border)', fontWeight: 600, fontSize: '0.85rem' }}>
              Files ({job.results.length})
            </div>
            <ul style={{ listStyle: 'none', maxHeight: 480, overflowY: 'auto' }}>
              {job.results.map((r) => (
                <li
                  key={r.file_path}
                  onClick={() => setSelectedFile(r)}
                  style={{
                    padding: '9px 12px',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    background: selectedFile?.file_path === r.file_path
                      ? 'rgba(124,106,247,0.15)' : 'transparent',
                    borderBottom: '1px solid var(--color-border)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span className={`badge badge-${r.status}`} style={{ fontSize: '0.65rem', padding: '1px 5px' }}>
                    {r.status}
                  </span>
                  {r.file_path.split(/[\\/]/).pop()}
                </li>
              ))}
            </ul>
          </div>

          {/* File detail */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {fileResult ? (
              <div className="card">
                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 12 }}>
                  {fileResult.file_path}
                </p>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: 0, marginBottom: 16, borderBottom: '1px solid var(--color-border)' }}>
                  {['diff', 'issues', 'ai-changes'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      style={{
                        background: 'none',
                        border: 'none',
                        borderBottom: activeTab === tab ? '2px solid var(--color-primary)' : '2px solid transparent',
                        padding: '8px 16px',
                        cursor: 'pointer',
                        color: activeTab === tab ? 'var(--color-primary)' : 'var(--color-text-muted)',
                        fontWeight: activeTab === tab ? 600 : 400,
                        fontSize: '0.875rem',
                      }}
                    >
                      {tab === 'diff' && `Diff (${fileResult.diff ? '✓' : '—'})`}
                      {tab === 'issues' && `Issues (${fileResult.issues.length})`}
                      {tab === 'ai-changes' && `AI Changes (${fileResult.ai_changes.length})`}
                    </button>
                  ))}
                </div>

                {activeTab === 'diff' && (
                  fileResult.original_code && fileResult.migrated_code
                    ? (
                      <div style={{ height: 600, marginBottom: 16 }}>
                        <MonacoDiffViewer
                          original={fileResult.original_code}
                          migrated={fileResult.migrated_code}
                          filePath={fileResult.file_path}
                          language="php"
                        />
                      </div>
                    )
                    : (
                      <DiffViewer diff={fileResult.diff} filePath={fileResult.file_path} />
                    )
                )}
                {activeTab === 'issues' && <IssueList issues={fileResult.issues} />}
                {activeTab === 'ai-changes' && (
                  fileResult.ai_changes.length === 0
                    ? <p style={{ color: 'var(--color-text-muted)' }}>No AI changes.</p>
               