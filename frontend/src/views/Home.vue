<template>
  <div class="home-container">
    <!-- Top Navigation Bar -->
    <nav class="navbar">
      <div class="nav-brand">MIROFISH</div>
      <div class="nav-links">
        <LanguageSelector />
        <a href="https://github.com/666ghj/MiroFish" target="_blank" class="github-link">
          {{ t('home.github') }} <span>↗</span>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-left">
          <div class="tag-row">
            <span class="orange-tag">{{ t('home.offlineEngine') }}</span>
            <span class="version-text">{{ t('home.version') }}</span>
          </div>

          <h1 class="main-title">
            {{ t('home.title1') }}<br>
            <span class="gradient-text">{{ t('home.title2') }}</span>
          </h1>

          <div class="hero-desc">
            <p v-html="t('home.desc1')"></p>
            <p class="slogan-text">
              {{ t('home.desc2') }}<span class="blinking-cursor">_</span>
            </p>
          </div>

          <div class="decoration-square"></div>
        </div>

        <div class="hero-right">
          <div class="logo-container">
            <img src="../assets/logo/MiroFish_logo_left.jpeg" alt="MiroFish Logo" class="hero-logo" />
          </div>
          <button class="scroll-down-btn" @click="scrollToBottom">↓</button>
        </div>
      </section>

      <!-- Dashboard: Two-Column Layout -->
      <section class="dashboard-section">
        <!-- Left Column: Status & Steps -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-dot">■</span> {{ t('home.statusTitle') }}
          </div>

          <h2 class="section-title">{{ t('home.readyTitle') }}</h2>
          <p class="section-desc">
            {{ t('home.readyDesc') }}
          </p>

          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-value">{{ t('home.metric1Val') }}</div>
              <div class="metric-label">{{ t('home.metric1Desc') }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">{{ t('home.metric2Val') }}</div>
              <div class="metric-label">{{ t('home.metric2Desc') }}</div>
            </div>
          </div>

          <div class="steps-container">
            <div class="steps-header">
               <span class="diamond-icon">◇</span> {{ t('home.workflowTitle') }}
            </div>
            <div class="workflow-list">
              <div v-for="(step, i) in steps" :key="i" class="workflow-item">
                <span class="step-num">{{ step.num }}</span>
                <div class="step-info">
                  <div class="step-title">{{ step.title }}</div>
                  <div class="step-desc">{{ step.desc }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Interactive Console -->
        <div class="right-panel">
          <div class="console-box">
            <div class="console-section">
              <div class="console-header">
                <span>{{ t('home.console1Title') }}</span>
                <span>{{ t('home.console1Sub') }}</span>
              </div>
              <div
                class="upload-zone"
                :class="[showErrorBorders && files.length === 0 ? 'error-pulse' : '', files.length > 0 ? 'has-files' : '']"
                @dragover.prevent="handleDragOver"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input ref="fileInput" type="file" multiple accept=".pdf,.md,.txt" @change="handleFileSelect" style="display: none" :disabled="loading" />
                <div v-if="files.length === 0" class="upload-placeholder">
                  <div class="upload-icon">↑</div>
                  <div class="upload-title">{{ t('home.dragDropTitle') }}</div>
                  <div class="upload-hint">{{ t('home.dragDropHint') }}</div>
                </div>
                <div v-else class="file-list">
                  <div v-for="(file, index) in files" :key="index" class="file-item">
                    <span>📄</span>
                    <span class="file-name">{{ file.name }}</span>
                    <button @click.stop="removeFile(index)" class="remove-btn">×</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="console-divider"><span>{{ t('home.parametersTitle') }}</span></div>

            <div class="console-section">
              <div class="console-header">
                <span>{{ t('home.console2Title') }}</span>
              </div>
              <div
                class="input-wrapper"
                :class="showErrorBorders && formData.simulationRequirement.trim() === '' ? 'error-pulse' : ''"
                @click="clearError"
              >
                <textarea v-model="formData.simulationRequirement" class="code-input" :placeholder="t('home.inputPlaceholder')" rows="6" :disabled="loading" @input="clearError"></textarea>
                <div class="model-badge">{{ t('home.engineBadge') }}</div>
              </div>
            </div>

            <div class="console-section btn-section">
              <Transition name="fade">
                <div v-if="showErrorPopup" class="error-notification">Completar pasos 1 y 2 antes de iniciar</div>
              </Transition>
              <button class="start-engine-btn" @click="startSimulation" :disabled="loading">
                <span v-if="!loading">{{ t('home.startBtn') }}</span>
                <span v-else>{{ t('home.initializing') }}</span>
                <span>→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <HistoryDatabase />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import LanguageSelector from '../components/LanguageSelector.vue'
import { useSettings } from '../store/settings.js'

const { t } = useSettings()

const router = useRouter()

const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const error = ref('')
const isDragOver = ref(false)
const fileInput = ref(null)
const showErrorBorders = ref(false)
const showErrorPopup = ref(false)

const clearError = () => {
  showErrorBorders.value = false
}

const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
})

const steps = computed(() => [
  { num: '01', title: t('home.step1Title'), desc: t('home.step1Desc') },
  { num: '02', title: t('home.step2Title'), desc: t('home.step2Desc') },
  { num: '03', title: t('home.step3Title'), desc: t('home.step3Desc') },
  { num: '04', title: t('home.step4Title'), desc: t('home.step4Desc') },
  { num: '05', title: t('home.step5Title'), desc: t('home.step5Desc') },
])

const triggerFileInput = () => {
  clearError()
  if (!loading.value) fileInput.value?.click()
}

const handleFileSelect = (event) => {
  clearError()
  addFiles(Array.from(event.target.files))
}

const handleDragOver = (e) => { isDragOver.value = true }
const handleDragLeave = (e) => { isDragOver.value = false }
const handleDrop = (e) => {
  clearError()
  isDragOver.value = false
  addFiles(Array.from(e.dataTransfer.files))
}

const addFiles = (newFiles) => {
  const allowed = ['.pdf', '.md', '.txt']
  const valid = newFiles.filter(f => allowed.some(ext => f.name.toLowerCase().endsWith(ext)))
  files.value = [...files.value, ...valid]
}

const removeFile = (index) => { files.value.splice(index, 1) }

const scrollToBottom = () => { window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }) }

const startSimulation = () => {
  if (!canSubmit.value) {
    showErrorBorders.value = true
    showErrorPopup.value = true
    setTimeout(() => {
      showErrorPopup.value = false
    }, 3000)
    return
  }
  showErrorBorders.value = false
  showErrorPopup.value = false
  if (loading.value) return
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement)
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}
</script>

<style scoped>
/* Global variables */
:root {
  --black: #000000;
  --white: #FFFFFF;
  --orange: #FF4500;
  --gray-light: #F5F5F5;
  --gray-text: #666666;
  --border: #E5E5E5;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.home-container {
  min-height: 100vh;
  background: var(--white);
  font-family: var(--font-sans);
  color: var(--black);
}

/* Navbar */
.navbar {
  height: 60px;
  background: var(--black);
  color: var(--white);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.nav-brand {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.2rem;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.github-link {
  color: var(--white);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: opacity 0.2s;
}

.github-link:hover { opacity: 0.8; }

/* Main content */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 40px;
}

/* Hero */
.hero-section {
  display: flex;
  justify-content: space-between;
  margin-bottom: 80px;
  position: relative;
}

.hero-left {
  flex: 1;
  padding-right: 60px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.orange-tag {
  background: var(--orange);
  color: var(--white);
  padding: 4px 10px;
  font-weight: 700;
  letter-spacing: 1px;
  font-size: 0.75rem;
}

.version-text {
  color: #999;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.main-title {
  font-size: 4.5rem;
  line-height: 1.2;
  font-weight: 500;
  margin: 0 0 40px 0;
  letter-spacing: -2px;
  color: var(--black);
}

.gradient-text {
  background: linear-gradient(90deg, #000 0%, #444 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.hero-desc {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--gray-text);
  max-width: 640px;
  margin-bottom: 50px;
  font-weight: 400;
  text-align: justify;
}

.hero-desc p { margin-bottom: 1.5rem; }

.slogan-text {
  font-size: 1.2rem;
  font-weight: 520;
  color: var(--black);
  letter-spacing: 1px;
  border-left: 3px solid var(--orange);
  padding-left: 15px;
  margin-top: 20px;
}

.blinking-cursor {
  color: var(--orange);
  animation: blink 1s step-end infinite;
  font-weight: 700;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.decoration-square {
  width: 16px;
  height: 16px;
  background: var(--orange);
}

.hero-right {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}

.logo-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  padding-right: 40px;
}

.hero-logo {
  max-width: 500px;
  width: 100%;
}

.scroll-down-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--orange);
  font-size: 1.2rem;
  transition: all 0.2s;
}

.scroll-down-btn:hover { border-color: var(--orange); }

/* Dashboard */
.dashboard-section {
  display: flex;
  gap: 60px;
  border-top: 1px solid var(--border);
  padding-top: 60px;
  align-items: flex-start;
}

.left-panel {
  flex: 0.8;
  display: flex;
  flex-direction: column;
}

.panel-header {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.status-dot { color: var(--orange); font-size: 0.8rem; }

.section-title {
  font-size: 2rem;
  font-weight: 520;
  margin: 0 0 15px 0;
}

.section-desc {
  color: var(--gray-text);
  margin-bottom: 25px;
  line-height: 1.6;
}

.metrics-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.metric-card {
  border: 1px solid var(--border);
  padding: 20px 30px;
  min-width: 150px;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 1.8rem;
  font-weight: 520;
  margin-bottom: 5px;
}

.metric-label { font-size: 0.85rem; color: #999; }

.steps-container {
  border: 1px solid var(--border);
  padding: 30px;
  position: relative;
}

.steps-header {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.diamond-icon { font-size: 1.2rem; line-height: 1; }

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.workflow-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.step-num {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--black);
  opacity: 0.3;
}

.step-info { flex: 1; }

.step-title {
  font-weight: 520;
  font-size: 1rem;
  margin-bottom: 4px;
}

.step-desc { font-size: 0.85rem; color: var(--gray-text); }

/* Right panel – Console */
.right-panel {
  flex: 1.2;
  display: flex;
  flex-direction: column;
}

.console-box {
  border: 1px solid #CCC;
  padding: 8px;
}

.console-section { padding: 20px; }

.console-section.btn-section { padding-top: 0; position: relative; }

.console-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #666;
}

.upload-zone {
  border: 1px dashed #CCC;
  height: 200px;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #FAFAFA;
}

.upload-zone.has-files { align-items: flex-start; }
.upload-zone:hover { background: #F0F0F0; border-color: #999; }

/* Error state */
.error-pulse {
  border: 2px solid red !important;
  background-color: #fff3f3 !important;
  transition: all 0.2s ease-in-out;
}

.error-notification {
  position: absolute;
  top: -44px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #ff4444;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: bold;
  z-index: 10;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  white-space: nowrap;
}

.upload-placeholder { text-align: center; }

.upload-icon {
  width: 40px;
  height: 40px;
  border: 1px solid #DDD;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  color: #999;
}

.upload-title {
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.upload-hint {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #999;
}

.file-list {
  width: 100%;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  background: var(--white);
  padding: 8px 12px;
  border: 1px solid #EEE;
  font-family: var(--font-mono);
  font-size: 0.85rem;
}

.file-name { flex: 1; margin: 0 10px; }

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
}

.console-divider {
  display: flex;
  align-items: center;
  margin: 10px 0;
  border-top: 1px solid #EEE;
}

.console-divider span {
  padding: 0 15px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #BBB;
  letter-spacing: 1px;
}

.input-wrapper {
  position: relative;
  border: 1px solid #DDD;
  background: #FAFAFA;
}

.code-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 20px;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 150px;
}

.model-badge {
  position: absolute;
  bottom: 10px;
  right: 15px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #AAA;
}

.start-engine-btn {
  width: 100%;
  background: var(--black);
  color: var(--white);
  border: none;
  padding: 20px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  letter-spacing: 1px;
}

.start-engine-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Fade transition for error popup */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
