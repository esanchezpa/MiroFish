import { ref, watch } from 'vue'
import { locales } from './locales.js'

export const language = ref(localStorage.getItem('mirofish_lang') || 'es')

watch(language, (newLang) => {
  localStorage.setItem('mirofish_lang', newLang)
})

export const useSettings = () => {
  const t = (key) => {
    const keys = key.split('.')
    let val = locales[language.value] || locales['es']
    for (const k of keys) {
      if (val === undefined) return key
      val = val[k]
    }
    return val || key
  }

  return {
    language,
    t
  }
}
