/**
 * Temporary storage for pending uploads and requirements.
 * v0.2: Added buildSettings snapshot so MainView receives the full config.
 */
import { reactive } from 'vue'

const state = reactive({
  files: [],
  simulationRequirement: '',
  buildSettings: null,    // v0.2: snapshot of buildSettings at Start time
  isPending: false
})

/**
 * @param {File[]} files
 * @param {string} requirement
 * @param {object|null} buildSettingsSnapshot  - snapshot from buildSettings store
 */
export function setPendingUpload(files, requirement, buildSettingsSnapshot = null) {
  state.files = files
  state.simulationRequirement = requirement
  state.buildSettings = buildSettingsSnapshot ? { ...buildSettingsSnapshot } : null
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    buildSettings: state.buildSettings,
    isPending: state.isPending
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.buildSettings = null
  state.isPending = false
}

export default state
