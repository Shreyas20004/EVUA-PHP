import { create } from 'zustand'

/**
 * Zustand store for migration state.
 *
 * Shape:
 * {
 *   uploadedFiles: File[],
 *   uploadId: string | null,
 *   savedPaths: string[],
 *   sourceVersion: string,
 *   targetVersion: string,
 *   dryRun: boolean,
 *   useMockAi: boolean,
 *   jobId: string | null,
 *   jobStatus: 'idle' | 'pending' | 'running' | 'completed' | 'failed',
 *   jobResult: object | null,
 *   error: string | null,
 * }
 */
const useMigrationStore = create((set) => ({
  // Upload stage
  uploadedFiles: [],
  uploadId: null,
  savedPaths: [],

  // Config stage
  sourceVersion: '5.6',
  targetVersion: '8.0',
  dryRun: false,
  useMockAi: false,

  // Job stage
  jobId: null,
  jobStatus: 'idle',
  jobResult: null,
  error: null,

  // Actions
  setUploadedFiles: (files) => set({ uploadedFiles: files }),
  setUploadResult: (uploadId, savedPaths) => set({ uploadId, savedPaths }),
  setSourceVersion: (v) => set({ sourceVersion: v }),
  setTargetVersion: (v) => set({ targetVersion: v }),
  setDryRun: (v) => set({ dryRun: v }),
  setUseMockAi: (v) => set({ useMockAi: v }),
  setJobId: (jobId) => set({ jobId }),
  setJobStatus: (jobStatus) => set({ jobStatus }),
  setJobResult: (jobResult) => set({ jobResult }),
  setError: (error) => set({ error }),

  reset: () =>
    set({
      uploadedFiles: [],
      uploadId: null,
      savedPaths: [],
      jobId: null,
      jobStatus: 'idle',
      jobResult: null,
      error: null,
    }),
}))

export default useMigrationStore
