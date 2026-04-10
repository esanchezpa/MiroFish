#CONTEXTO_IMPL1
Tu caso real hoy es este:

corpus dominado por 15 PDFs = 16.1 MB
53 MDs = 173 KB, o sea casi no pesan frente a los PDFs
en tu corrida se extrajeron 2,819,028 caracteres
el build llegó a batch 496/2860 (3 chunks) y luego cayó con 403 forbidden: Account is over the episode usage limit

Eso confirma 3 cosas:

el problema no es la ontología
el problema está en chunking + batches + episodes 1:1
necesitas configuración visible + estimador + guardrails antes de disparar el build
Config ideal para tu caso
Perfil recomendado: free_tier_large_corpus
{
  "profile_name": "free_tier_large_corpus",
  "chunk_size": 4000,
  "chunk_overlap": 120,
  "boundary_min_fill_ratio": 0.80,
  "min_chunk_chars": 2200,
  "batch_size": 12,
  "episode_pack_size": 1,
  "hard_stop_episode_threshold": 850,
  "warn_episode_threshold": 700,
  "pdf_cleanup_enabled": true,
  "remove_repeated_headers_footers": true,
  "normalize_whitespace": true,
  "max_rounds_preview": 48,
  "enable_graph_memory_update": false,
  "boost_mode": "auto",
  "show_advanced_controls": true
}
Por qué esta config

Con 2,819,028 chars y esta config:

chunks estimados
⌈
(
2819028
−
120
)
/
(
4000
−
120
)
⌉
≈
727
⌈(2819028−120)/(4000−120)⌉≈727
episodes estimados

Como episode_pack_size = 1:

~727 episodes
batches estimados

Con batch_size = 12:

ceil(727 / 12) = 61 batches
Resultado

Pasas de algo tipo:

2860 batches de 3
a algo como:
61 batches de 12

Ese cambio solo ya es brutal.

Qué stats debería mostrar esta config
Antes del build

Con el texto ya extraído, el sistema debe mostrar:

total_extracted_chars: 2,819,028
estimated_chunks: ~727
estimated_episodes: ~727
estimated_batches: ~61
estimated_ontology_tokens_input
estimated_ontology_tokens_output
estimated_ontology_tokens_total
estimated_build_time_min
estimated_build_time_max
Estimación razonable para tu caso
Ontología

La repo ya limita el texto enviado al LLM de ontología a 50,000 chars, no manda los 2.8M completos.
Entonces la ontología no explota por corpus gigante.

Estimación sana:

input ontology: ~14k–17k tokens
output ontology: ~2k–4k tokens
total ontology: ~16k–21k tokens
Tiempo ontología

Por tu log real:

exitoso: aprox. 35–45 segundos

Yo mostraría:

avg ontology time: ~40s
con etiqueta: based on last successful run
Build del grafo

Con la config propuesta:

episodes: ~727
batches: ~61
tiempo estimado: 7 a 18 min

Yo en UI mostraría:

estimated_graph_build_time: 7–18 min
quota_risk: LOW
zep_free_tier_fit: YES
Tokens con boost y sin boost

Acá hay una precisión importante.

Cómo funciona hoy tu repo

En run_parallel_simulation.py:

Twitter usa LLM normal
Reddit usa boost si está configurado
o si no hay boost, Reddit también cae al LLM normal

Entonces:

Sin boost
todo el gasto de simulación cae en el proveedor principal
Con boost
Twitter sigue usando el proveedor principal
Reddit pasa al proveedor boost
Ojo

Eso normalmente no cambia mucho el volumen total de tokens
Lo que cambia es:

cómo se reparten por proveedor
la velocidad/concurrencia
y eventualmente el costo si los precios son distintos
Entonces la UI no debería mentir

No pongas:

“boost reduce tokens”

porque no necesariamente los reduce.

Pon:

Estimated simulation tokens (total)
Primary provider tokens
Boost provider tokens
Mode: off / auto
Para preview mode

Si dejas:

max_rounds_preview = 48
dos plataformas
actividad media

yo estimaría algo como:

total simulation tokens: ~500k a 900k

Y en boost_mode = auto:

primary: ~50%
boost: ~50%

Esto es una estimación inicial.
La versión seria del sistema debe recalibrarse con runs reales.

Qué UI agregar
Ubicación del botón

Viendo tu Home actual, la tuerca debe ir en la barra superior, dentro de nav-links, al lado de LanguageSwitcher.

Y en la vista de proceso, repetir la misma tuerca en el header-right, para poder ajustar config también después de entrar al flujo.

Componente nuevo

Crear:

frontend/src/components/SettingsDrawer.vue

Y opcionalmente:

frontend/src/components/ConfigStatsPanel.vue
Comportamiento

La tuerca abre un drawer lateral derecho, no un modal centrado.
Razón: no tapa todo y se siente más “tooling/workbench”.

Tabs dentro del drawer

Usa 4 tabs:

1. Build
chunk size
overlap
batch size
hard stop threshold
warning threshold
2. Cleaning
remove repeated headers/footers
normalize whitespace
PDF cleanup on/off
boundary min fill ratio
min chunk chars
3. Simulation
max rounds preview
boost mode
graph memory update on/off
4. Stats
extracted chars
estimated chunks
estimated episodes
estimated batches
ontology avg time
graph avg time
simulation avg time
ontology tokens
simulation tokens total
primary/boost token split
last run actuals
Qué debe pasar funcionalmente
En Home

El usuario:

sube archivos
abre tuerca
ajusta config
ve estimación preliminar

Al dar Start:

se guarda un snapshot de config junto con pendingUpload
En Process/Main

Cuando arranca el build:

se usa esa config
no la default hardcodeada
Antes de lanzar build

Debe ejecutarse un chequeo:

si estimated_episodes > hard_stop_episode_threshold
bloquear build
mostrar banner rojo
explicar: “esta corrida probablemente superará tu cuota de Zep”

Esto te ahorra otra quemada de cuota.