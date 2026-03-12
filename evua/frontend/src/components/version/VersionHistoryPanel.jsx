import { useState, useEffect, useCallback } from 'react'
import { getVersionHistory, previewRevert, applyRevert } from '../../services/versionApi.js'

const STAGE_COLORS = {
  initial:      '#6b7280',
  risk_assessed:'#f59e0b',
  ai_verified:  '#8b5cf6',
  reverted:     '#3b82f6',
  migrated:     '#10b981',
}

function CommitCard({ version, isLatest, onRevert }) {
  const short = version.commit_hash?.slice(0, 7) ?? '???????'
  const stageColor = STAGE_COLORS[version.migration_stage] ?? '#6b7280'
  const date = version.created_at
    ? new Date(version.created_at).toLocaleString()
    : '—'

  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        paddingBottom: 20,
        position: 'relative',
      }}
    >
      {/* Timeline spine */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24, flexShrink: 0 }}>
        <div style={{
          width: 12, height: 12, borderRadius: '50%',
          background: isLatest ? 'var(--color-primary)' : stageColor,
          border: '2px solid var(--color-border)',
          zIndex: 1,
          marginTop: 4,
        }} />
        <div style={{ flex: 1, width: 2, background: 'var(--color-border)', marginTop: 2 }} />
      </div>

      {/* Commit info */}
      <div style={{
        flex: 1,
        background: 'var(--color-surface)',
        border: `1px solid ${isLatest ? 'var(--color-primary)' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius)',
        padding: '10px 14px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
          <code style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', background: 'var(--color-bg)', padding: '1px 6px', borderRadius: 4 }}>
            {short}
          </code>
          {version.migration_stage && (
            <span style={{ fontSize: '0.7rem', padding: '1px 7px', borderRadius: 10, background: stageColor + '22', color: stageColor, fontWeight: 600 }}>
              {version.migration_stage}
            </span>
          )}
          {isLatest && (
            <span style={{ fontSize: '0.7rem', padding: '1px 7px', borderRadius: 10, background: 'rgba(124,106,247,0.15)', color: 'var(--color-primary)', fontWeight: 600 }}>
              CURRENT
            </span>
          )}
        </div>

        <p style={{ margin: '0 0 6px', fontSize: '0.875rem', color: 'var(--color-text)' }}>
          {version.commit_message || 'No message'}
        </p>

        <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem', color: 'var(--color-text-muted)', flexWrap: 'wrap' }}>
          <span>{date}</span>
          {version.files_changed != null && <span>{version.files_changed} file{version.files_changed !== 1 ? 's' : ''}</span>}
          {version.insertions > 0 && <span style={{ color: '#10b981' }}>+{version.insertions}</span>}
          {version.deletions > 0  && <span style={{ color: '#ef4444' }}>−{version.deletions}</span>}
        </div>

        {!isLatest && (
          <button
            onClick={() => onRevert(version)}
            style={{
              marginTop: 10,
              padding: '5px 12px',
              fontSize: '0.8rem',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 6,
              cursor: 'pointer',
              color: 'var(--color-text)',
            }}
          >
            ↩ Revert to this version
          </button>
        )}
      </div>
    </div>
  )
}

function RevertModal({ jobId, version, onClose, onSuccess }) {
  const [preview, setPreview]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [applying, setApplying] = useState(false)
  const [error, setError]       = useState(null)

  useEffect(() => {
    previewRevert(jobId, version.commit_hash)
      .then(setPreview)
      .catch((e) => setError(e.response?.data?.detail ?? e.message))
      .finally(() => setLoading(false))
  }, [jobId, version.commit_hash])

  const confirm = async () => {
    setApplying(true)
    try {
      const result = await applyRevert(jobId, version.commit_hash)
      onSuccess(result)
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message)
      setApplying(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)',
        padding: 24,
        maxWidth: 480,
        width: '90%',
      }}>
        <h3 style={{ margin: '0 0 8px' }}>Revert to commit <code>{version.commit_hash?.slice(0, 7)}</code></h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 16px' }}>
          This creates a <strong>new commit</strong> restoring the code to this state. Nothing is deleted — the full history is preserved.
        </p>

        {loading && <p style={{ color: 'var(--color-text-muted)' }}>Loading preview…</p>}
        {error   && <p style={{ color: 'var(--color-danger)' }}>Error: {error}</p>}

        {preview && !error && (
          <div style={{
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
            borderRadius: 6,
            padding: '10px 14px',
            marginBottom: 16,
            fontSize: '0.8rem',
            color: 'var(--color-text-muted)',
          }}>
            <strong style={{ color: 'var(--color-text)' }}>Preview</strong>
            <p style={{ margin: '6px 0 0' }}>{preview.changes?.description ?? 'Reverts to selected commit state.'}</p>
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            disabled={applying}
            style={{ padding: '7px 16px', border: '1px solid var(--color-border)', borderRadius: 6, cursor: 'pointer', background: 'transparent', color: 'var(--color-text)', fontSize: '0.875rem' }}
          >
            Cancel
          </button>
          <button
            onClick={confirm}
            disabled={applying || loading || !!error}
            style={{ padding: '7px 16px', border: 'none', borderRadius: 6, cursor: 'pointer', background: 'var(--color-primary)', color: '#fff', fontSize: '0.875rem' }}
          >
            {applying ? 'Reverting…' : 'Confirm Revert'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function VersionHistoryPanel({ jobId }) {
  const [history, setHistory]       = useState(null)
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [revertTarget, setRevertTarget] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    getVersionHistory(jobId)
      .then(setHistory)
      .catch((e) => {
        const status = e.response?.status
        if (status === 404) {
          setHistory({ versions: [], total_versions: 0 })
        } else {
          setError(e.response?.data?.detail ?? e.message)
        }
      })
      .finally(() => setLoading(false))
  }, [jobId])

  useEffect(() => { load() }, [load])

  const handleRevertSuccess = (result) => {
    setRevertTarget(null)
    setSuccessMsg(`Reverted — new commit ${result.to_commit?.slice(0, 7)}`)
    load()
  }

  if (loading) return <p style={{ color: 'var(--color-text-muted)' }}>Loading history…</p>
  if (error)   return <p style={{ color: 'var(--color-danger)' }}>Error: {error}</p>

  const versions = history?.versions ?? []

  if (versions.length === 0) {
    return (
      <div style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', padding: '12px 0' }}>
        No version history yet. Version snapshots are created during migration.
      </div>
    )
  }

  return (
    <div>
      {successMsg && (
        <div style={{
          background: 'rgba(16,185,129,0.1)', border: '1px solid #10b981',
          borderRadius: 6, padding: '8px 14px', marginBottom: 16,
          fontSize: '0.875rem', color: '#10b981',
          display: 'flex', justifyContent: 'space-between',
        }}>
          {successMsg}
          <button onClick={() => setSuccessMsg(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#10b981' }}>✕</button>
        </div>
      )}

      <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 16 }}>
        {versions.length} snapshot{versions.length !== 1 ? 's' : ''} — newest first
      </p>

      <div style={{ paddingTop: 4 }}>
        {versions.map((v, i) => (
          <CommitCard
            key={v.commit_hash ?? i}
            version={v}
            isLatest={i === 0}
            onRevert={setRevertTarget}
          />
        ))}
      </div>

      {revertTarget && (
        <RevertModal
          jobId={jobId}
          version={revertTarget}
          onClose={() => setRevertTarget(null)}
          onSuccess={handleRevertSuccess}
        />
      )}
    </div>
  )
}
