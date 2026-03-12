import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadZone from '../components/migration/UploadZone.jsx'
import VersionSelector from '../components/migration/VersionSelector.jsx'
import JobProgress from '../components/migration/JobProgress.jsx'
import { useMigration } from '../hooks/useMigration.js'

export default function MigratePage() {
  const navigate = useNavigate()
  const {
    sourceVersion,
    targetVersion,
    dryRun,
    useMockAi,
    jobId,
    jobStatus,
    jobResult,
    savedPaths,
    error,
    setSourceVersion,
    setTargetVersion,
    setDryRun,
    setUseMockAi,
    upload,
    migrate,
  } = useMigration()

  const [uploading, setUploading] = useState(false)
  const [migrating, setMigrating] = useState(false)

  const handleFiles = async (files) => {
    if (!files.length) return
    setUploading(true)
    try {
      await upload(files)
    } finally {
      setUploading(false)
    }
  }

  const handleMigrate = async () => {
    setMigrating(true)
    try {
      const jid = await migrate()
      if (jid) {
        // Navigation will happen once job completes — watch jobStatus
      }
    } finally {
      setMigrating(false)
    }
  }

  // Navigate to results when done
  if (jobStatus === 'completed' && jobId) {
    navigate(`/results/${jobId}`)
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <h1 style={{ marginBottom: 24 }}>Migrate PHP Files</h1>

      {error && (
        <div style={{
          background: 'rgba(239,68,68,0.1)',
          border: '1px solid var(--color-danger)',
          borderRadius: 6,
          padding: '12px 16px',
          marginBottom: 16,
          color: 'var(--color-danger)',
        }}>
          {error}
        </div>
      )}

      {/* Step 1: Upload */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h2 style={{ marginBottom: 12 }}>1. Upload PHP Files</h2>
        <UploadZone onFiles={handleFiles} />
        {uploading && <p style={{ color: 'var(--color-text-muted)', marginTop: 8 }}>Uploading…</p>}
        {savedPaths.length > 0 && (
          <p style={{ color: 'var(--color-success)', marginTop: 8, fontSize: '0.85rem' }}>
            ✓ {savedPaths.length} file(s) ready
          </p>
        )}
      </div>

      {/* Step 2: Configure */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h2 style={{ marginBottom: 12 }}>2. Configure Migration</h2>
        <VersionSelector
          sourceVersion={sourceVersion}
          targetVersion={targetVersion}
          onSourceChange={setSourceVersion}
          onTargetChange={setTargetVersion}
        />
        <div style={{ display: 'flex', gap: 20, marginTop: 8 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
            />
            <span style={{ fontSize: '0.875rem' }}>Dry run (no file changes)</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useMockAi}
              onChange={(e) => setUseMockAi(e.target.checked)}
            />
            <span style={{ fontSize: '0.875rem' }}>Use mock AI (no API key needed)</span>
          </label>
        </div>
      </div>

      {/* Step 3: Run */}
      <div className="card">
        <h2 style={{ marginBottom: 12 }}>3. Run Migration</h2>
        <button
          className="btn btn-primary"
          disabled={!savedPaths.length || migrating || ['pending', 'running'].includes(jobStatus)}
          onClick={handleMigrate}
        >
          {migrating || ['pending', 'running'].includes(jobStatus) ? 'Running…' : 'Migrate'}
        </button>

        {jobStatus !== 'idle' && (
          <JobProgress
            status={jobStatus}
            totalFiles={jobResult?.total_files ?? savedPaths.length}
            completed={jobResult?.completed ?? 0}
            failed={jobResult?.failed ?? 0}
          />
        )}
      </div>
    </div>
  )
}
