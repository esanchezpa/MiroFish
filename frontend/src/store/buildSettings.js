import { reactive, watch } from 'vue'

/**
 * Build Settings Store — MiroFish v0.2
 * Separate from settings.js (i18n/language store)
 * Profile: free_tier_large_corpus
 * For 2.8M chars: ~727 chunks, ~61 batches with these defaults
 */

export const defaultBuildSettings = {
  // --- Chunking ---
  chunkSize: 4000,
  chunkOverlap: 120,
  boundaryMinFillRatio: 0.80,
  minChunkChars: 2200,
  // --- Batching ---
  batchSize: 12,
  episodePackSize: 1,
  // --- Quota Guardrails ---
  hardStopEpisodeThreshold: 850,
  warnEpisodeThreshold: 700,
  // --- PDF Cleanup ---
  pdfCleanupEnabled: true,
  removeRepeatedHeadersFooters: true,
  normalizeWhitespace: true,
  // --- Simulation ---
  maxRoundsPreview: 48,
  enableGraphMemoryUpdate: false,
  boostMode: 'auto',    // 'off' | 'auto'
  // Internal
  version: 1
}

const STORAGE_KEY = 'mirofish.buildSettings.v1'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...defaultBuildSettings }
    const saved = JSON.parse(raw)
    // Merge: new keys from defaultBuildSettings are added gracefully
    return { ...defaultBuildSettings, ...saved }
  } catch {
    return { ...defaultBuildSettings }
  }
}

export const buildSettings = reactive(loadFromStorage())

// Auto-persist on any change
watch(buildSettings, (val) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...val }))
  } catch (e) {
    console.warn('[buildSettings] Failed to persist to localStorage:', e)
  }
}, { deep: true })

export const resetBuildSettings = () => {
  Object.assign(buildSettings, defaultBuildSettings)
}

/**
 * Estimate chunks/episodes/batches for a given text length and settings.
 * This is a fast local estimate — the accurate one requires calling /api/graph/estimate.
 */
export const estimateLocally = (totalChars, settings = buildSettings) => {
  const { chunkSize, chunkOverlap, batchSize, hardStopEpisodeThreshold, warnEpisodeThreshold } = settings
  const effectiveStep = chunkSize - chunkOverlap
  const estimatedChunks = Math.ceil((totalChars - chunkOverlap) / effectiveStep)
  const estimatedBatches = Math.ceil(estimatedChunks / batchSize)

  let quotaRisk = 'low'
  if (estimatedChunks >= hardStopEpisodeThreshold) quotaRisk = 'high'
  else if (estimatedChunks >= warnEpisodeThreshold) quotaRisk = 'medium'

  return {
    estimatedChunks,
    estimatedEpisodes: estimatedChunks,
    estimatedBatches,
    quotaRisk,
    zepFreeTierFit: estimatedChunks < hardStopEpisodeThreshold
  }
}
