/**
 * Axios client pointing at the FastAPI backend.
 * The Vite dev proxy rewrites /api and /health to the backend URL.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
export const getHealth = () => api.get('/health')

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------

/**
 * Upload one or more PHP files.
 * @param {FileList|File[]} files
 * @returns {Promise<{upload_id: string, files: string[]}>}
 */
export const uploadFiles = async (files) => {
  const form = new FormData()
  for (const f of files) form.append('files', f)
  const resp = await api.post('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return resp.data
}

// ---------------------------------------------------------------------------
// Migration
// ---------------------------------------------------------------------------

/**
 * Start a migration job.
 * @param {{
 *   source_version: string,
 *   target_version: string,
 *   file_paths: string[],
 *   output_dir?: string,
 *   dry_run?: boolean,
 *   use_mock_ai?: boolean,
 * }} params
 * @returns {Promise<{job_id: string, status: string}>}
 */
export const startMigration = async (params) => {
  const resp = await api.post('/api/migrate', params)
  return resp.data
}

/**
 * Poll a migration job's status.
 * @param {string} jobId
 * @returns {Promise<object>}
 */
export const getJobStatus = async (jobId) => {
  const resp = await api.get(`/api/jobs/${jobId}`)
  return resp.data
}

/**
 * List all jobs.
 */
export const listJobs = async () => {
  const resp = await api.get('/api/jobs')
  return resp.data
}

export default api
