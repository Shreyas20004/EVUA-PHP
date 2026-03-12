import { useCallback, useState } from 'react'

const PHP_VERSIONS = ['5.6', '7.0', '7.4', '8.0', '8.1', '8.2', '8.3']

export default function VersionSelector({
  sourceVersion,
  targetVersion,
  onSourceChange,
  onTargetChange,
}) {
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <div className="form-group" style={{ flex: 1, minWidth: 140 }}>
        <label className="form-label">Source PHP Version</label>
        <select
          value={sourceVersion}
          onChange={(e) => onSourceChange(e.target.value)}
        >
          {PHP_VERSIONS.map((v) => (
            <option key={v} value={v}>
              PHP {v}
            </option>
          ))}
        </select>
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 8 }}>
        <span style={{ color: 'var(--color-primary)', fontSize: '1.2rem' }}>→</span>
      </div>
      <div className="form-group" style={{ flex: 1, minWidth: 140 }}>
        <label className="form-label">Target PHP Version</label>
        <select
          value={targetVersion}
          onChange={(e) => onTargetChange(e.target.value)}
        >
          {PHP_VERSIONS.filter((v) => v > sourceVersion).map((v) => (
            <option key={v} value={v}>
              PHP {v}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
