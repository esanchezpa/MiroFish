<template>
  <div class="language-selector">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" class="globe-icon">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="2" y1="12" x2="22" y2="12"></line>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
    </svg>
    <select v-model="language" class="lang-select" @change="syncVueI18n">
      <option value="es">Español (LA)</option>
      <option value="en">English</option>
    </select>
  </div>
</template>

<script setup>
import { useSettings } from '../store/settings'

const { language } = useSettings()

// Sync with vue-i18n if available in the app
const syncVueI18n = () => {
  try {
    localStorage.setItem('locale', language.value)
    document.documentElement.lang = language.value
  } catch (e) {
    // Silently ignore if vue-i18n is not accessible
  }
}
</script>

<style scoped>
.language-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f5f5f5;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid #eaeaea;
  transition: all 0.2s;
}

.language-selector:hover {
  background: #fff;
  border-color: #ddd;
}

.globe-icon {
  color: #666;
}

.lang-select {
  border: none;
  background: transparent;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  cursor: pointer;
  outline: none;
  appearance: none;
  padding-right: 14px;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23333333%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right center;
  background-size: 8px auto;
}
</style>
