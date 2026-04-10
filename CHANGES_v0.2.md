# CHANGES.md — Bitácora de Implementación MiroFish v0.2
> Config + Stats + Chunks | Iniciado: 2026-04-10 09:33 PDT

---

## v0.2 — feat(config-stats-chunks)

### [2026-04-10 09:34 PDT] — Sprint 2: Backend

#### `backend/app/config.py`
- Cambio `DEFAULT_CHUNK_SIZE`: 500 → **4000**
- Cambio `DEFAULT_CHUNK_OVERLAP`: 50 → **120**
- Añadido `DEFAULT_BATCH_SIZE = 12`
- Añadido `DEFAULT_BOUNDARY_MIN_FILL_RATIO = 0.80`
- Añadido `DEFAULT_MIN_CHUNK_CHARS = 2200`
- Añadido `DEFAULT_EPISODE_PACK_SIZE = 1`
- Añadido `DEFAULT_WARN_EPISODE_THRESHOLD = 700`
- Añadido `DEFAULT_HARD_STOP_EPISODE_THRESHOLD = 850`

#### `backend/app/models/project.py`
- Añadido campo `batch_size: int = 12` al dataclass `Project`
- Añadido campo `boundary_min_fill_ratio: float = 0.80`
- Añadido campo `min_chunk_chars: int = 2200`
- Añadido campo `episode_pack_size: int = 1`
- Añadido campo `pdf_cleanup_enabled: bool = True`
- Añadido campo `remove_repeated_headers_footers: bool = True`
- Añadido campo `normalize_whitespace: bool = True`
- Añadido campo `build_stats: Dict[str, Any] = field(default_factory=dict)`
- Añadido campo `simulation_stats: Dict[str, Any] = field(default_factory=dict)`
- `to_dict()` extendido con todos los campos nuevos
- `from_dict()` usa `.get('field', default)` → backward-compatible con proyectos viejos

#### `backend/app/utils/file_parser.py`
- `split_text_into_chunks()` signature extendida:
  - Nuevos params: `boundary_min_fill_ratio=0.80`, `min_chunk_chars=2200`
- Defaults actualizados: `chunk_size=4000`, `overlap=120`
- Nueva lógica de boundary: solo acepta corte si `candidate_len >= min_chunk_chars AND >= chunk_size * boundary_min_fill_ratio`
- Fallback duro a `end = start + chunk_size` si no hay separador válido
- Resultado esperado: ~727 chunks para corpus 2.8M chars (vs ~2860 antes)

#### `backend/app/services/text_processor.py`
- `split_text()` extendido con `boundary_min_fill_ratio` y `min_chunk_chars`
- Nuevos defaults: `chunk_size=4000`, `overlap=120`
- Propaga params al `split_text_into_chunks()`

#### `backend/app/api/graph.py`
- **FIX CRÍTICO**: `batch_size=3` hardcodeado → ahora lee del request y del proyecto
- Lee config del request: `chunk_size`, `chunk_overlap`, `batch_size`, `boundary_min_fill_ratio`, `min_chunk_chars`, `episode_pack_size`, `pdf_cleanup_enabled`, `remove_repeated_headers_footers`, `normalize_whitespace`
- Guarda config en `project` antes de lanzar el thread de build
- `TextProcessor.split_text()` recibe todos los nuevos params
- `add_text_batches()` recibe `batch_size` dinámico (no hardcoded 3)
- **Guardrail pre-build**: bloquea si `estimated_episodes > 850` con error claro
- **stats reales**: al completar guarda en `project.build_stats`: chunks, batches, nodes, edges, elapsed_ms, batch_size_used, chunk_size_used, last_run_at
- **Nuevo endpoint**: `POST /api/graph/estimate` — estima chunks/episodes/batches/tokens/tiempos sin ejecutar build real

---

### [2026-04-10 09:35 PDT] — Sprint 1: Frontend

#### `frontend/src/store/buildSettings.js` [NUEVO]
- Store reactivo separado de `settings.js` (i18n)
- `defaultBuildSettings` con todos los valores del perfil `free_tier_large_corpus`
- Persistencia en `localStorage` key `mirofish.buildSettings.v1`
- Merge inteligente al cargar (backward-compatible con claves nuevas)
- `resetBuildSettings()` para restaurar defaults

#### `frontend/src/store/pendingUpload.js` [MODIFICADO]
- State extendido con campo `buildSettings: null`
- `setPendingUpload(files, req, settingsSnapshot)` recibe y guarda snapshot
- `clearPendingUpload()` resetea también `buildSettings`
- `getPendingUpload()` devuelve también `buildSettings`

#### `frontend/src/components/SettingsDrawer.vue` [NUEVO]
- Drawer lateral derecho (no modal centrado)
- 4 tabs: Build / Cleaning / Simulation / Stats
- Modo simple (controles esenciales visibles) + Modo avanzado (toggle `show_advanced`)
- Tab Stats: estimaciones en tiempo real del corpus y último run real
- Integra `buildSettings` store reactivo
- Botón "Resetear defaults" en footer

#### `frontend/src/views/Home.vue` [MODIFICADO]
- Añadido botón `⚙` en `nav-links` junto a `LanguageSelector`
- Estado `settingsOpen` + `<SettingsDrawer>`
- `startSimulation()` incluye snapshot de `buildSettings` en `setPendingUpload()`

#### `frontend/src/views/MainView.vue` [MODIFICADO]
- Lee `pendingUpload.buildSettings` vía `getPendingUpload()`
- `buildGraph()` recibe objeto extendido con todos los params de config
- Botón `⚙` también en `header-right` del workbench
- Guardrail visual: si `estimated_episodes > 850` muestra banner rojo antes del build

#### `frontend/src/api/graph.js` [MODIFICADO]
- Añadida función `estimateGraph(params)` → `POST /api/graph/estimate`

---

### [2026-04-10 09:36 PDT] — Revisión final

- Verificado backward-compatibility: `from_dict()` usa defaults para campos nuevos
- Verificado que sin abrir settings, el build usa `chunk_size=4000, batch_size=12`
- Verificado que el endpoint `/estimate` no requiere Zep API key (solo lee texto local)
- Verificado que la UI no miente sobre tokens (se muestra como estimación con método heurístico)

---

## Resumen de impacto

| Métrica | Antes | Después |
|---|---|---|
| `chunk_size` default | 500 | **4000** |
| `batch_size` | 3 (hardcoded) | **12** (configurable) |
| Chunks para 2.8M chars | ~5638 | **~727** |
| Batches para 2.8M chars | ~1879 | **~61** |
| Riesgo de cuota Zep | ALTO (crasheó en batch 496) | **BAJO** |
| Guardrail cuota | ✗ | **✓ (bloquea en >850 episodes)** |
| Stats reales post-build | ✗ | **✓** |
| Config desde UI | ✗ | **✓ (SettingsDrawer)** |
