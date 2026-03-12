import { useCallback, useRef } from 'react'
import { getJobStatus, startMigration, uploadFiles } from '../services/api.js'
import useMigrationStore from '../store/migrationStore.js'

const POLL_INTERVAL_MS = 2000

/**
 * Custom hook that drives the full migration workflow:
 * 1. Upload files → get savedPaths
 * 2. Start migration job → get jobId
 * 3. Poll until completed / failed
 */
export function useMigration() {
  const store = useMigrationStore()
  const pollRef = useRef(null)

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const startPolling = useCallback(
    (jobId) => {
      stopPolling()
      pollRef.current = setInterval(async () => {
        try {
          const data = await getJobStatus(jobId)
          store.setJobStatus(data.status)
          if (data.status === 'completed' || data.status === 'failed') {
            store.setJobResult(data)
            stopPolling()
          }
        } catch (err) {
          store.setError(err.message)
          stopPolling()
        }
      }, POLL_INTERVAL_MS)
    },
    [store]
  )

  const upload = useCallback(
    async (files) => {
      store.setError(null)
      store.setUploadedFiles(Array.from(files))
      try {
        const result = await uploadFiles(files)
        store.setUploadResult(result.upload_id, result.files)
        return result.files
      } catch (err) {
        store.setError(err.response?.data?.detail || err.message)
        throw err
      }
    },
    [store]
  )

  const migrate = useCallback(async () => {
    store.setError(null)
    store.setJobStatus('pending')
    try {
      const result = await startMigration({
        source_version: store.sourceVersion,
        target_version: store.targetVersion,
        file_paths: store.savedPaths,
        dry_run: store.dryRun,
        use_mock_ai: store.useMockAi,
      })
      store.setJobId(result.job_id)
      store.setJobStatus(result.status)
      startPolling(result.job_id)
      return result.job_id
    } catch (err) {
      store.setError(err.response?.data?.detail || err.message)
      store.setJobStatus('failed')
      throw err
    }
  }, [store, startPolling])

  return {
    ...store,
    upload,
    migrate,
    stopPolling,
  }
}
