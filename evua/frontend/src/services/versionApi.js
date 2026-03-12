import api from './api.js'

export const getVersionHistory = async (jobId) => {
  const resp = await api.get(`/api/versions/${jobId}/history`)
  return resp.data
}

export const previewRevert = async (jobId, targetCommit) => {
  const resp = await api.get(`/api/versions/${jobId}/revert-preview`, {
    params: { target_commit: targetCommit },
  })
  return resp.data
}

export const applyRevert = async (jobId, targetCommit) => {
  const resp = await api.post(`/api/versions/${jobId}/revert`, null, {
    params: { target_commit: targetCommit },
  })
  return resp.data
}

export const getVersionDiff = async (jobId, fromCommit, toCommit) => {
  const resp = await api.get(`/api/versions/${jobId}/diff`, {
    params: { from_commit: fromCommit, to_commit: toCommit },
  })
  return resp.data
}
