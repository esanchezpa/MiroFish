<template>
  <!-- Overlay -->
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="open" class="drawer-overlay" @click.self="close" />
    </Transition>
    <Transition name="drawer-slide">
      <aside v-if="open" class="settings-drawer" role="dialog" aria-label="Build Settings">
        <!-- Header -->
        <div class="drawer-header">
          <div class="drawer-title">
            <span class="drawer-icon">⚙</span>
            <span>{{ t('settings.title') || 'Build Settings' }}</span>
          </div>
          <button class="drawer-close" @click="close" aria-label="Close">✕</button>
        </div>

        <!-- Tabs -->
        <div class="drawer-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="drawer-tab"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <!-- Tab Content -->
        <div class="drawer-body">

          <!-- TAB: Build -->
          <div v-if="activeTab === 'build'" class="tab-pane">
            <div class="section-label">Chunking</div>

            <div class="field-row">
              <label>Chunk Size <span class="badge">chars</span></label>
              <div class="field-input-group">
                <input type="number" v-model.number="settings.chunkSize" min="500" max="16000" step="500" />
                <span class="field-hint">Rec: 4000</span>
              </div>
            </div>

            <div class="field-row">
              <label>Overlap <span class="badge">chars</span></label>
              <div class="field-input-group">
                <input type="number" v-model.number="settings.chunkOverlap" min="0" max="500" step="20" />
                <span class="field-hint">Rec: 120</span>
              </div>
            </div>

            <div class="field-row">
              <label>Batch Size</label>
              <div class="field-input-group">
                <input type="number" v-model.number="settings.batchSize" min="1" max="50" step="1" />
                <span class="field-hint">Rec: 12</span>
              </div>
            </div>

            <div class="divider" />
            <div class="section-label">Quota Guardrails</div>

            <div class="field-row">
              <label>Hard Stop <span class="badge badge-red">episodes</span></label>
              <div class="field-input-group">
                <input type="number" v-model.number="settings.hardStopEpisodeThreshold" min="100" max="2000" step="50" />
                <span class="field-hint">Free tier ≈ 850</span>
              </div>
            </div>

            <div class="field-row">
              <label>Warn Threshold <span class="badge badge-yellow">episodes</span></label>
              <div class="field-input-group">
                <input type="number" v-model.number="settings.warnEpisodeThreshold" min="100" max="2000" step="50" />
              </div>
            </div>

            <!-- Advanced toggle -->
            <button class="advanced-toggle" @click="showAdvanced = !showAdvanced">
              {{ showAdvanced ? '▲ Hide advanced' : '▼ Show advanced' }}
            </button>

            <template v-if="showAdvanced">
              <div class="divider" />
              <div class="section-label">Advanced Chunking</div>

              <div class="field-row">
                <label>Min Fill Ratio</label>
                <div class="field-input-group">
                  <input type="number" v-model.number="settings.boundaryMinFillRatio" min="0.3" max="1.0" step="0.05" />
                  <span class="field-hint">0.80 = 80% of chunk_size</span>
                </div>
              </div>

              <div class="field-row">
                <label>Min Chunk Chars</label>
                <div class="field-input-group">
                  <input type="number" v-model.number="settings.minChunkChars" min="0" max="5000" step="100" />
                </div>
              </div>

              <div class="field-row">
                <label>Episode Pack Size</label>
                <div class="field-input-group">
                  <input type="number" v-model.number="settings.episodePackSize" min="1" max="10" step="1" />
                </div>
              </div>
            </template>
          </div>

          <!-- TAB: Cleaning -->
          <div v-if="activeTab === 'cleaning'" class="tab-pane">
            <div class="section-label">PDF Cleanup</div>
            <p class="section-desc">
              Applied before chunking. Reduces junk chars in PDF-heavy corpora.
            </p>

            <div class="toggle-row">
              <label>PDF Cleanup</label>
              <input type="checkbox" v-model="settings.pdfCleanupEnabled" class="toggle" />
            </div>

            <div class="toggle-row" :class="{ disabled: !settings.pdfCleanupEnabled }">
              <label>Remove Repeated Headers/Footers</label>
              <input type="checkbox" v-model="settings.removeRepeatedHeadersFooters"
                     :disabled="!settings.pdfCleanupEnabled" class="toggle" />
            </div>

            <div class="toggle-row" :class="{ disabled: !settings.pdfCleanupEnabled }">
              <label>Normalize Whitespace</label>
              <input type="checkbox" v-model="settings.normalizeWhitespace"
                     :disabled="!settings.pdfCleanupEnabled" class="toggle" />
            </div>

            <div class="divider" />
            <div class="section-label">Advanced</div>

            <div class="field-row">
              <label>Min Fill Ratio</label>
              <input type="number" v-model.number="settings.boundaryMinFillRatio" min="0.3" max="1.0" step="0.05" />
            </div>

            <div class="field-row">
              <label>Min Chunk Chars</label>
              <input type="number" v-model.number="settings.minChunkChars" min="0" max="5000" step="100" />
            </div>
          </div>

          <!-- TAB: Simulation -->
          <div v-if="activeTab === 'simulation'" class="tab-pane">
            <div class="section-label">Preview Mode</div>

            <div class="field-row">
              <label>Max Rounds (Preview)</label>
              <div class="field-input-group">
                <input type="number" v-model.number="settings.maxRoundsPreview" min="1" max="200" step="4" />
                <span class="field-hint">Rec: 48</span>
              </div>
            </div>

            <div class="divider" />
            <div class="section-label">Boost Mode</div>

            <div class="radio-group">
              <label class="radio-label">
                <input type="radio" v-model="settings.boostMode" value="off" />
                <span><strong>Off</strong> — all traffic on primary LLM</span>
              </label>
              <label class="radio-label">
                <input type="radio" v-model="settings.boostMode" value="auto" />
                <span><strong>Auto</strong> — Twitter=primary, Reddit=boost</span>
              </label>
            </div>

            <div class="divider" />
            <div class="toggle-row">
              <label>Graph Memory Update</label>
              <input type="checkbox" v-model="settings.enableGraphMemoryUpdate" class="toggle" />
            </div>
            <p class="section-desc">
              Enables live Zep graph memory updates during simulation.
              May increase quota usage.
            </p>
          </div>

          <!-- TAB: Stats -->
          <div v-if="activeTab === 'stats'" class="tab-pane">
            <!-- Live estimate -->
            <div class="section-label">Local Estimate</div>
            <div v-if="localEstimate" class="stats-grid">
              <div class="stat-card" :class="riskClass">
                <div class="stat-value">{{ localEstimate.estimatedChunks.toLocaleString() }}</div>
                <div class="stat-label">Estimated Chunks / Episodes</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ localEstimate.estimatedBatches.toLocaleString() }}</div>
                <div class="stat-label">Estimated Batches</div>
              </div>
              <div class="stat-card" :class="riskClass">
                <div class="stat-value">{{ quotaRiskLabel }}</div>
                <div class="stat-label">Quota Risk</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ localEstimate.zepFreeTierFit ? '✓ YES' : '✗ NO' }}</div>
                <div class="stat-label">Zep Free Tier Fit</div>
              </div>
            </div>
            <p v-else class="section-desc">No corpus loaded yet. Upload files to see estimates.</p>

            <!-- Last real build stats -->
            <template v-if="lastBuildStats && Object.keys(lastBuildStats).length">
              <div class="divider" />
              <div class="section-label">Last Build (Actual)</div>
              <div class="stats-grid stats-grid-3">
                <div class="stat-card">
                  <div class="stat-value">{{ lastBuildStats.actual_chunks?.toLocaleString() ?? '—' }}</div>
                  <div class="stat-label">Chunks</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ lastBuildStats.actual_batches?.toLocaleString() ?? '—' }}</div>
                  <div class="stat-label">Batches</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ lastBuildStats.actual_episodes?.toLocaleString() ?? '—' }}</div>
                  <div class="stat-label">Episodes</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ lastBuildStats.node_count?.toLocaleString() ?? '—' }}</div>
                  <div class="stat-label">Nodes</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ lastBuildStats.edge_count?.toLocaleString() ?? '—' }}</div>
                  <div class="stat-label">Edges</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">
                    {{ lastBuildStats.build_elapsed_ms
                       ? Math.round(lastBuildStats.build_elapsed_ms / 1000) + 's'
                       : '—' }}
                  </div>
                  <div class="stat-label">Build Time</div>
                </div>
              </div>
              <p class="last-run-at">Last run: {{ lastBuildStats.last_run_at ?? 'unknown' }}</p>
            </template>

            <div class="info-note">
              ℹ Token estimates are heuristic (chars/3.8 for ontology, rounds×agents×900 for simulation).
              Values update after a real build run.
            </div>
          </div>

        </div>

        <!-- Footer -->
        <div class="drawer-footer">
          <button class="btn-reset" @click="reset">↺ Reset Defaults</button>
          <button class="btn-done" @click="close">Done</button>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { buildSettings, resetBuildSettings, estimateLocally } from '@/store/buildSettings'
import { useSettings } from '@/store/settings'

const { t } = useSettings()

const props = defineProps({
  open: { type: Boolean, default: false },
  totalChars: { type: Number, default: 0 },      // from Home/MainView corpus
  lastBuildStats: { type: Object, default: null } // from project.build_stats
})
const emit = defineEmits(['update:open'])

// Use the reactive store directly (two-way binding)
const settings = buildSettings

const activeTab = ref('build')
const showAdvanced = ref(false)

const tabs = [
  { id: 'build',      icon: '🔧', label: 'Build'      },
  { id: 'cleaning',   icon: '🧹', label: 'Cleaning'   },
  { id: 'simulation', icon: '▶',  label: 'Simulation' },
  { id: 'stats',      icon: '📊', label: 'Stats'      }
]

// Local estimate (computed from current settings + totalChars)
const localEstimate = computed(() => {
  if (!props.totalChars) return null
  return estimateLocally(props.totalChars, settings)
})

const riskClass = computed(() => {
  if (!localEstimate.value) return ''
  const r = localEstimate.value.quotaRisk
  return r === 'high' ? 'risk-high' : r === 'medium' ? 'risk-medium' : 'risk-low'
})

const quotaRiskLabel = computed(() => {
  const r = localEstimate.value?.quotaRisk ?? 'unknown'
  return r.toUpperCase()
})

function close() {
  emit('update:open', false)
}

function reset() {
  if (confirm('Reset all build settings to defaults?')) {
    resetBuildSettings()
  }
}
</script>

<style scoped>
/* ---- Overlay + Drawer ---- */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
}

.settings-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 380px;
  max-width: 95vw;
  background: #1a1d2e;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 40px rgba(0, 0, 0, 0.5);
}

/* ---- Transitions ---- */
.drawer-fade-enter-active, .drawer-fade-leave-active { transition: opacity 0.25s ease; }
.drawer-fade-enter-from, .drawer-fade-leave-to { opacity: 0; }

.drawer-slide-enter-active, .drawer-slide-leave-active { transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1); }
.drawer-slide-enter-from, .drawer-slide-leave-to { transform: translateX(100%); }

/* ---- Header ---- */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.drawer-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
}
.drawer-icon { font-size: 1.1rem; }
.drawer-close {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: color 0.15s, background 0.15s;
}
.drawer-close:hover { color: #e2e8f0; background: rgba(255, 255, 255, 0.06); }

/* ---- Tabs ---- */
.drawer-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.drawer-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 0.6rem 0.25rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #64748b;
  font-size: 0.7rem;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.drawer-tab .tab-icon { font-size: 1rem; }
.drawer-tab.active { color: #7c6af7; border-bottom-color: #7c6af7; }
.drawer-tab:hover:not(.active) { color: #94a3b8; }

/* ---- Body ---- */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
}

.tab-pane { display: flex; flex-direction: column; gap: 0.75rem; }

.section-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7c6af7;
  margin-top: 0.25rem;
}
.section-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
}
.divider { height: 1px; background: rgba(255, 255, 255, 0.06); margin: 0.5rem 0; }

/* ---- Field rows ---- */
.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.field-row label {
  font-size: 0.8rem;
  color: #cbd5e1;
  min-width: 120px;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.field-input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
input[type="number"] {
  width: 90px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #e2e8f0;
  padding: 0.3rem 0.5rem;
  font-size: 0.85rem;
  text-align: right;
  outline: none;
  transition: border-color 0.15s;
}
input[type="number"]:focus { border-color: #7c6af7; }
.field-hint { font-size: 0.7rem; color: #475569; white-space: nowrap; }

.badge {
  font-size: 0.6rem;
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(124, 106, 247, 0.2);
  color: #a78bfa;
  font-weight: 600;
}
.badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.badge-yellow { background: rgba(234, 179, 8, 0.15); color: #facc15; }

/* ---- Toggle rows ---- */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #cbd5e1;
}
.toggle-row.disabled { opacity: 0.4; pointer-events: none; }
.toggle { width: 36px; height: 20px; accent-color: #7c6af7; cursor: pointer; }

/* ---- Radio group ---- */
.radio-group { display: flex; flex-direction: column; gap: 0.5rem; }
.radio-label {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #cbd5e1;
  cursor: pointer;
}
.radio-label input { margin-top: 2px; accent-color: #7c6af7; }

/* ---- Advanced toggle ---- */
.advanced-toggle {
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.75rem;
  cursor: pointer;
  padding: 0;
  text-align: left;
  transition: color 0.15s;
}
.advanced-toggle:hover { color: #94a3b8; }

/* ---- Stats grid ---- */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}
.stats-grid-3 { grid-template-columns: 1fr 1fr 1fr; }

.stat-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  text-align: center;
}
.stat-value { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; }
.stat-label { font-size: 0.65rem; color: #64748b; margin-top: 2px; }

.risk-high .stat-value { color: #f87171; }
.risk-medium .stat-value { color: #facc15; }
.risk-low .stat-value { color: #4ade80; }

.last-run-at { font-size: 0.7rem; color: #475569; text-align: right; margin: 0; }

.info-note {
  font-size: 0.7rem;
  color: #475569;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  line-height: 1.5;
  margin-top: 0.5rem;
}

/* ---- Footer ---- */
.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.btn-reset {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #64748b;
  padding: 0.4rem 0.875rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.btn-reset:hover { color: #94a3b8; border-color: rgba(255, 255, 255, 0.2); }
.btn-done {
  background: #7c6af7;
  border: none;
  color: #fff;
  padding: 0.4rem 1.25rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-done:hover { background: #6d5ce6; }
</style>
