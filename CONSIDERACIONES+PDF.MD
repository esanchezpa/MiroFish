Técnica avanzada para PDF-heavy corpora

Como tus PDFs dominan el peso, yo metería una limpieza opcional antes del chunking.

En FileParser o en un paso de normalización:

hacer:

remover headers repetidos por página
remover footers repetidos
unir palabras cortadas por salto de línea
colapsar saltos múltiples
remover páginas casi vacías
remover índices/TOC si están repetidos

Eso puede bajar mucho:

chars inútiles
chunks
episodes
ruido del grafo
No tocaría
el cap de 50k chars para ontología
eso ya está bien
Diseño del drawer para no romper UX
Modo simple

Visible por default:

chunk size
overlap
batch size
hard stop threshold
max rounds preview
boost mode
Modo avanzado

Colapsable:

boundary min fill ratio
min chunk chars
cleanup flags
episode pack size

Así el usuario normal no se pierde y tú sí tienes control fino.

Orden de implementación recomendado para el agentico
Sprint 1
crear settings store
crear SettingsDrawer.vue
agregar gear en Home.vue
persistir config en pendingUpload
enviar config en buildGraph
Sprint 2
extender Project para persistir config
hacer batch_size configurable
extender splitter con boundary_min_fill_ratio y min_chunk_chars
agregar endpoint /api/graph/estimate
Sprint 3
mostrar Stats tab con estimator real
guardar métricas reales de ontología/build
mostrar last run actuals
Sprint 4
instrumentar estimación de simulación
separar tokens por primary/boost
agregar hard stop pre-build
Sprint 5
cleanup PDF opcional
warning banner de quota
fallback y migración para proyectos viejos
Criterios de aceptación

El cambio está bien hecho si pasa esto:

sin abrir settings, MiroFish sigue funcionando como antes
con la config nueva, el build usa esos valores reales
el estimator calcula chunks exactos sobre el texto extraído del proyecto
si el estimate supera 850 episodes, el sistema bloquea por defecto
la UI muestra métricas reales del último run
el sistema distingue claramente:
estimado
real
primary
boost
si faltan campos en proyectos viejos, se rellenan con defaults sin romper carga