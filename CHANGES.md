# Historial de Cambios Implementados (CHANGES.md)

**Última actualización:** 2026-04-09 01:13 PDT

---

## 1. Internacionalización (i18n) del Frontend
**Fecha:** 2026-04-08

Se completó la migración de la interfaz del usuario al español como idioma por defecto, con soporte dinámico Español/Inglés.

### Archivos Modificados:
- `frontend/src/store/locales.js` — Diccionario central de traducciones (Single Source of Truth)
- `frontend/src/store/settings.js` — Hook `useSettings()` + función `t()` reactiva
- `frontend/src/views/Home.vue`
- `frontend/src/views/MainView.vue`
- `frontend/src/components/Step1GraphBuild.vue`
- `frontend/src/components/Step2EnvSetup.vue` (script automatizado masivo)
- `frontend/src/components/Step3Simulation.vue` (script automatizado masivo)
- `frontend/src/components/Step4Report.vue` (script automatizado masivo)
- `frontend/src/components/Step5Interaction.vue` (botones de descarga TXT, MD, PDF, Imprimir)
- `i18n_updater.py` — Herramienta Python de reemplazo masivo vía regex

---

## 2. Ajuste en Backend (ReportAgent)
**Fecha:** 2026-04-08

- Restaurado `backend/app/api/report.py` para que no restrinja la generación de reportes exclusivamente a inglés, permitiendo soporte multi-idioma según el selector del frontend.

---

## 3. Mejoras de UX / UI en Home.vue
**Fecha:** 2026-04-08

- **Validación interactiva:** El botón "Iniciar Motor" ya no se deshabilita estáticamente; en su lugar activa validaciones visuales activas.
- **Animación de error:** Las zonas de arrastre (Step 1) y el campo de prompt (Step 2) parpadean con contorno rojo si están vacíos al intentar iniciar.
- **Popup de notificación:** Mensaje *"Completar pasos 1 y 2 antes de iniciar"* con animación de desvanecimiento (fade), duración 3 segundos.
- **Bordes persistentes:** Los campos en error mantienen borde rojo hasta que el usuario interactúa con ellos (clic, escritura o carga de archivo).

---

## 4. Botones de Exportación en Step5 (Reportes)
**Fecha:** 2026-04-08

- Añadidos botones funcionales con iconos en el panel de reportes:
  - Descargar como **TXT**
  - Descargar como **Markdown (MD)**
  - Guardar como **PDF**
  - **Imprimir**

---

## 5. Protección de Navegación — Guardia de Salida (Navigation Guard)
**Fecha:** 2026-04-09

### Problema
El usuario podía salir accidentalmente de la "Mesa de Trabajo" (`/process/:projectId`) usando el botón Atrás del navegador, el botón Atrás del mouse, o el logo del encabezado, sin confirmación previa.

### Solución implementada en `frontend/src/views/MainView.vue`

> **Nota:** La ruta `/process/:projectId` es renderizada por `MainView.vue`, no por `Process.vue`.
> En `router/index.js`, el import dice `import Process from '../views/MainView.vue'` — el alias es histórico, el componente real es `MainView.vue`.

**Lógica añadida (mínima y sin efectos secundarios sobre el resto del componente):**

```js
// Estado del guard
const showExitModal = ref(false)
let pendingRoute = null
let allowLeave = false

// goHome() — reemplaza el router.push('/') directo del logo
const goHome = () => { pendingRoute = '/'; showExitModal.value = true }

// Confirmar salida
const confirmExit = () => {
  allowLeave = true
  router.push(pendingRoute || '/').finally(() => { allowLeave = false; pendingRoute = null })
}

// Cancelar
const cancelExit = () => { showExitModal.value = false; pendingRoute = null }

// Guard SPA (botón atrás del navegador + router.push + router-link)
onBeforeRouteLeave((to) => {
  if (allowLeave) return true
  pendingRoute = to.fullPath
  showExitModal.value = true
  return false
})

// Guard para cerrar pestaña / recargar
const handleBeforeUnload = (e) => { e.preventDefault(); e.returnValue = '' }
```

**Cobertura de casos:**

| Escenario | Mecanismo |
|---|---|
| Botón Atrás del navegador / mouse | `onBeforeRouteLeave` (Vue Router 4 intercepta popstate) |
| `router.push()` interno | `onBeforeRouteLeave` |
| Clic en logo MIROFISH OFFLINE | `goHome()` → modal directo |
| Cerrar pestaña / Recargar / Ctrl+W | `beforeunload` (mensaje genérico del navegador) |

**Modal custom añadido al template:**
- Título: *"Cancelar mesa de trabajo"*
- Texto: *"¿Desea regresar al inicio y cancelar la mesa de trabajo?"*
- Botones: `No, quedarse` / `Sí, salir`
- Estilos integrados en `<style scoped>` (clases `.exit-modal-overlay`, `.exit-modal`, etc.)

### Archivos Modificados:
- `frontend/src/views/MainView.vue` — lógica de guard + modal + estilos
- `frontend/src/router/index.js` — solo aclaración de comentario (sin cambio funcional)

---

## Resumen de Bugs Descartados Durante el Proceso

| Intento | Por qué falló |
|---|---|
| Guard en `Process.vue` | `Process.vue` **nunca se monta** en `/process/:projectId`; la ruta carga `MainView.vue` |
| `window.confirm()` nativo | Navegadores Chromium bloquean silenciosamente `confirm()` durante `popstate` |
| `popstate` + `pushState` sentinel | Conflicto directo con el propio listener `popstate` de Vue Router, causando loops |
| `onBeforeRouteLeave` con `next(false)` | Sintaxis incorrecta para Vue Router 4 (usa `return false`, no `next(false)`) |
| Guard global `router.beforeEach` | Funciona, pero más complejo de limpiar; `onBeforeRouteLeave` es suficiente en el componente correcto |
