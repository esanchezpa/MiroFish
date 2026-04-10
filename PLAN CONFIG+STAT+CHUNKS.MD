Plan técnico de implementación
Fase 1: persistencia de config sin romper nada
Frontend

Crear store:

frontend/src/store/settings.js

Schema:

export const defaultSettings = {
  chunkSize: 4000,
  chunkOverlap: 120,
  boundaryMinFillRatio: 0.8,
  minChunkChars: 2200,
  batchSize: 12,
  episodePackSize: 1,
  hardStopEpisodeThreshold: 850,
  warnEpisodeThreshold: 700,
  pdfCleanupEnabled: true,
  removeRepeatedHeadersFooters: true,
  normalizeWhitespace: true,
  maxRoundsPreview: 48,
  enableGraphMemoryUpdate: false,
  boostMode: 'auto',
  version: 1
}

Persistencia:

localStorage
key: mirofish.settings.v1
Cambios
frontend/src/views/Home.vue

Agregar:

botón tuerca en nav-links
estado settingsOpen
drawer
enviar config al store pendingUpload
frontend/src/store/pendingUpload.js

Extender:

const state = reactive({
  files: [],
  simulationRequirement: '',
  settings: null,
  isPending: false
})

y guardar/restaurar settings.

frontend/src/views/MainView.vue

Cuando hace:

buildGraph({ project_id: currentProjectId.value })

cambiar por:

buildGraph({
  project_id: currentProjectId.value,
  chunk_size: settings.chunkSize,
  chunk_overlap: settings.chunkOverlap,
  batch_size: settings.batchSize,
  boundary_min_fill_ratio: settings.boundaryMinFillRatio,
  min_chunk_chars: settings.minChunkChars,
  episode_pack_size: settings.episodePackSize,
  pdf_cleanup_enabled: settings.pdfCleanupEnabled,
  remove_repeated_headers_footers: settings.removeRepeatedHeadersFooters,
  normalize_whitespace: settings.normalizeWhitespace
})
Fase 2: backend acepta config extendida
Archivos a tocar
backend/app/config.py
backend/app/models/project.py
backend/app/api/graph.py
backend/app/services/text_processor.py
backend/app/utils/file_parser.py
backend/app/services/graph_builder.py
config.py

Agregar defaults nuevos:

DEFAULT_BATCH_SIZE = 12
DEFAULT_BOUNDARY_MIN_FILL_RATIO = 0.80
DEFAULT_MIN_CHUNK_CHARS = 2200
DEFAULT_EPISODE_PACK_SIZE = 1
DEFAULT_WARN_EPISODE_THRESHOLD = 700
DEFAULT_HARD_STOP_EPISODE_THRESHOLD = 850
project.py

Extender Project con:

batch_size: int = 12
boundary_min_fill_ratio: float = 0.8
min_chunk_chars: int = 2200
episode_pack_size: int = 1
pdf_cleanup_enabled: bool = True
remove_repeated_headers_footers: bool = True
normalize_whitespace: bool = True
build_stats: Dict[str, Any] = field(default_factory=dict)
simulation_stats: Dict[str, Any] = field(default_factory=dict)

Y en to_dict() / from_dict() soportar defaults para no romper proyectos viejos.

Fase 3: arreglar el splitter para que no fragmente de más

Hoy el problema grande está acá:

el split acepta cortar si encuentra separador después del 30%
eso genera chunks demasiado chicos
Cambio

Modificar split_text_into_chunks() para aceptar:

def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    boundary_min_fill_ratio: float = 0.8,
    min_chunk_chars: int = 0
):
Nueva lógica

En vez de:

aceptar cualquier separador desde chunk_size * 0.3

hacer:

buscar separadores cerca del final
aceptar solo si:
candidate_pos >= chunk_size * boundary_min_fill_ratio
y candidate_len >= min_chunk_chars
Regla recomendada
si no hay separador válido, usar end = start + chunk_size
Pseudocódigo
window = text[start:end]
candidate_end = None

for sep in separators:
    pos = window.rfind(sep)
    if pos != -1:
        real_end = start + pos + len(sep)
        candidate_len = real_end - start
        if candidate_len >= min_chunk_chars and candidate_len >= chunk_size * boundary_min_fill_ratio:
            candidate_end = real_end
            break

if candidate_end:
    end = candidate_end
else:
    end = start + chunk_size
Resultado esperado
menos micro-fragmentos
chunks mucho más llenos
episodios mucho más controlados
Fase 4: batch size configurable y métricas reales

Hoy graph.py fuerza:

batch_size=3

Eso hay que quitarlo.

backend/app/api/graph.py

Leer del request:

batch_size = data.get('batch_size', project.batch_size or Config.DEFAULT_BATCH_SIZE)

y guardarlo en proyecto.

Luego:

episode_result = builder.add_text_batches(
    graph_id,
    chunks,
    batch_size=batch_size,
    progress_callback=add_progress_callback
)
Mejorar retorno de add_text_batches

No devuelvas solo episode_uuids.

Devuelve algo tipo:

{
  "episode_uuids": [...],
  "episodes_sent": 727,
  "batches_sent": 61,
  "send_elapsed_ms": 92341,
  "failed_batch": null
}

Eso te sirve para stats reales.

Fase 5: estimator endpoint

Crear endpoint nuevo:

POST /api/graph/estimate
Input
{
  "project_id": "proj_xxx",
  "chunk_size": 4000,
  "chunk_overlap": 120,
  "boundary_min_fill_ratio": 0.8,
  "min_chunk_chars": 2200,
  "batch_size": 12,
  "episode_pack_size": 1,
  "max_rounds_preview": 48,
  "boost_mode": "auto"
}
Qué debe hacer
cargar extracted_text real del proyecto
correr el splitter real con esa config
calcular:
exact_chunks
exact_estimated_episodes
exact_estimated_batches
estimar tokens de ontología
estimar tiempo build
estimar tiempo/tokens simulación preview
Output
{
  "success": true,
  "data": {
    "total_extracted_chars": 2819028,
    "exact_chunks": 727,
    "estimated_episodes": 727,
    "estimated_batches": 61,
    "zep_free_tier_fit": true,
    "quota_risk": "low",
    "ontology_tokens": {
      "input": 15500,
      "output": 2800,
      "total": 18300
    },
    "graph_build_time_minutes": {
      "min": 7,
      "max": 18
    },
    "simulation_preview": {
      "max_rounds": 48,
      "estimated_total_tokens": 620000,
      "estimated_primary_tokens_no_boost": 620000,
      "estimated_primary_tokens_with_boost": 310000,
      "estimated_boost_tokens_with_boost": 310000
    }
  }
}
Fase 6: stats reales, no solo estimados
Ontología

En generate_ontology():

capturar start = time.time()
al terminar guardar en project.build_stats
project.build_stats["ontology_duration_ms_last"] = ...
project.build_stats["ontology_duration_ms_avg"] = ...
project.build_stats["ontology_input_chars_used"] = min(total_text_length, 50000)
Build del grafo

En build_task() guardar:

actual chunk count
actual episode count
actual batch count
send elapsed
wait elapsed
total build elapsed
final nodes / edges
Simulación

En simulation_runner.py y/o run_parallel_simulation.py guardar:

total rounds
total actions
elapsed seconds
provider mode
boost enabled
estimated primary tokens
estimated boost tokens

No inventes “tokens exactos” si la librería no te los expone.
Guarda:

estimated_tokens
method = heuristic o method = tokenizer

Eso es mucho más honesto.

Cómo estimar tokens técnicamente
Ontología

Como sí controlas el prompt:

usa tiktoken si el modelo es compatible
si no, fallback:
estimated_tokens = ceil(chars / 4)

para inglés/mixto técnico

o más conservador:

estimated_tokens = ceil(chars / 3.5)
Simulación

Como OASIS/Camel no te da fácil el usage exacto en esta repo, usa estimación por acción:

estimated_sim_tokens =
  total_rounds
  * avg_active_agents_per_round
  * avg_tokens_per_agent_turn
  * enabled_platforms
Defaults iniciales
avg_active_agents_per_round = midpoint(agents_per_hour_min, agents_per_hour_max)
avg_tokens_per_agent_turn = 900

y luego calibra con runs reales.

Qué mostrar en el panel de Stats
Bloque 1: corpus
PDFs count
MDs count
uploaded bytes
extracted chars
extracted chars after cleanup
Bloque 2: graph build estimate
chunk size
overlap
exact chunks
exact episodes
exact batches
free tier fit
risk badge
Bloque 3: runtime
avg ontology time
avg graph build time
avg simulation time
last successful run time
Bloque 4: tokens
ontology estimated tokens
simulation estimated tokens
primary provider tokens
boost provider tokens
mode: no boost / auto
Bloque 5: actual last run
actual chunks
actual episodes sent
actual batches sent
actual nodes
actual edges
failure reason if any