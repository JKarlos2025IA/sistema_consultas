# Roadmap de Mejoras — Sistema RAG Normativo
> **Última actualización:** 23 de Febrero 2026
> **Sistema:** Hub RAG Local + Cloud (sistemaconsultas-2026.streamlit.app)

---

## Leyenda de Prioridad

| Símbolo | Significado |
|---|---|
| 🔴 ALTA | Impacto directo en calidad de resultados |
| 🟡 MEDIA | Mejora experiencia o cobertura |
| 🟢 BAJA | Optimización o feature adicional |
| ✅ HECHO | Implementado |

---

## BLOQUE 1 — Calidad de Embeddings (Motor de Búsqueda)

### ✅ Chunks con título del artículo (23-Feb-2026)
- **Qué:** Cada chunk ahora empieza con `[Ley 32069]\nArtículo 57.- Declaratoria de desierto: ...`
- **Archivos modificados:**
  - `G:\Mi unidad\03_PROJECTS\0003_Scprits\Sistema_procesamiento_documental\modulos\embeddings.py`
  - `G:\Mi unidad\03_PROJECTS\0003_Scprits\Embedding_Legal\generar_embeddings.py`
- **PENDIENTE:** Reprocesar todas las fuentes con `--force` (ver sección Instrucciones)

---

### 🔴 Reprocesar todos los embeddings con mejora de chunks
**Qué:** Ejecutar regeneración con `--force` en todas las fuentes activas para que los cambios tengan efecto.

**Instrucciones por tipo de fuente:**

#### Leyes y Directivas (usan `modulos/embeddings.py`)
```bash
# Desde Sistema_procesamiento_documental, ejecutar etapa 7 con --force
# Fuentes afectadas:
# - 002_Ley_27444
# - 003_Decreto_Legistativo_1017
# - 004_Ley_reglamento_30225
# - 005_Ley_reglamento_32069
# - 001_Directivas_oece_2025
# - 001_Directivas_oece_2026
```

#### Opiniones OECE (usan `generar_embeddings.py`)
```bash
python "G:\Mi unidad\03_PROJECTS\0003_Scprits\Embedding_Legal\generar_embeddings.py" ^
    "CARPETA_JSON_OPINIONES" ^
    "G:\Mi unidad\01_BASE_NORMATIVA\000_CONSULTAS\02_BIBLIOTECA_NORMATIVA\006_Opiniones_2025_OECE" ^
    --force
```

> **Nota:** Después de regenerar, el motor crea `chunks.json` automáticamente en la primera carga. No es necesario hacer nada más.

---

### 🔴 Agregar título del artículo al chunk para fuentes sin etiqueta automática
**Problema actual:** `_extraer_etiqueta_norma()` cubre las 7 normas conocidas. Si se agrega una nueva norma con nombre no reconocido, no se etiqueta.
**Solución:** Ampliar la función `_extraer_etiqueta_norma()` al agregar una nueva fuente.
**Esfuerzo:** Bajo (1 línea de código)

---

### 🔴 Reprocesar Opiniones 2024, 2023, 2022
**Qué:** Las opiniones de años anteriores no están indexadas.
**Impacto:** Amplía enormemente la cobertura de criterios OSCE.
**Prerequisito:** Obtener los TXT/PDFs de las opiniones históricas.
**Esfuerzo:** Medio (ejecutar pipeline existente sobre nuevos archivos)

---

### 🟡 Modelo de embeddings legal especializado
**Problema:** `paraphrase-multilingual-MiniLM-L12-v2` es genérico. No entiende que "buena pro" ≈ "adjudicación" ≈ "ganador del proceso".
**Opciones:**
1. `multilingual-e5-large` (Microsoft) — mejor que MiniLM, mismo idioma
2. Fine-tuning sobre pares legales peruanos (complejo, requiere GPU)
3. Esperar modelos legales especializados en español peruano (no existen aún)
**Solución inmediata:** Usar `multilingual-e5-large` (requiere cambiar CONFIG_EMB y reprocesar)
**Esfuerzo:** Medio — cambiar modelo + reprocesar todos los índices

---

### 🟡 Metadata filtering (filtrar por fecha/número de artículo)
**Qué:** Poder buscar "artículos vigentes desde 2024" o "Artículo 57 específicamente".
**Implementación:** FAISS no soporta filtros; usar FAISS + filtro post-búsqueda sobre metadata.
**Dónde:** `motor_busqueda.py` — agregar filtro en `search()` antes del rerank.
**Esfuerzo:** Medio

---

## BLOQUE 2 — Cobertura de Normas

### 🔴 Agregar Opiniones OECE 2026
**Estado:** No procesadas aún.
**Proceso:** Parser → Embeddings → Agregar fuente en interfaz.

### 🔴 Agregar normas JNJ específicas
**Qué:** Reglamentos y directivas internas de la Junta Nacional de Justicia.
**Proceso:** igual al de cualquier nueva fuente.

### 🟡 Resoluciones relevantes TCP (Tribunal de Contrataciones)
**Qué:** Resoluciones del Tribunal que interpretan la Ley 32069.
**Valor:** Jurisprudencia administrativa + criterios vinculantes.

### 🟢 Directivas de otros organismos (OSCE, MEF, CGR)
**Qué:** Directivas de control, directivas de tesorería, etc.
**Esfuerzo:** Bajo si ya están en PDF accesible.

---

## BLOQUE 3 — Motor de Búsqueda

### 🟡 Reducir de 2 llamadas a DeepSeek a 1 por consulta
**Problema actual:** Cada consulta hace 2 llamadas API:
1. `deepseek-chat` — reformular query + expandir
2. `deepseek-r1` — generar respuesta con Chain of Thought

**Propuesta:** Hacer reformulación+expansión con el mismo modelo R1 en un solo prompt. O usar modelo local (Ollama) para la reformulación.
**Beneficio:** 40-50% menos latencia y costo API.
**Esfuerzo:** Medio

---

### 🟡 Cache inteligente por similaridad semántica
**Problema actual:** El cache usa hash exacto (query + sources). Dos preguntas sinónimas no comparten cache.
**Solución:** Al hacer la búsqueda vectorial, si el top resultado tiene score > 0.99 y está en cache, retornar respuesta cacheada.
**Esfuerzo:** Medio-Alto

---

### 🟢 Indexación incremental automática en el motor
**Qué:** Cuando el motor arranca y detecta una nueva norma en `fuentes_usuario.json` que no tiene `chunks.json`, procesarla en background.
**Beneficio:** Zero-config al agregar nuevas fuentes.
**Esfuerzo:** Alto

---

## BLOQUE 4 — Interfaz y UX

### 🟡 Panel de administración de fuentes mejorado
**Qué:** Vista de estado del sistema — vectores por fuente, última actualización, tamaño, errores.
**Beneficio:** Diagnóstico rápido sin abrir código.
**Esfuerzo:** Medio

### 🟡 Exportar historial de consultas a Excel
**Qué:** Botón para descargar `04_LOGS/` como Excel con columnas: fecha, consulta, fuentes, respuesta.
**Beneficio:** Auditoría de uso + revisión de calidad de respuestas.
**Esfuerzo:** Bajo

### 🟢 Modo de cita directa (sin IA)
**Qué:** Opción "Solo retrievar, sin generar respuesta". Muestra los chunks relevantes sin pasar por DeepSeek R1.
**Beneficio:** Más rápido, zero costo API, útil para búsqueda exploratoria.
**Esfuerzo:** Bajo (ya existe la lógica de búsqueda, solo separar del paso de generación)

---

## BLOQUE 5 — Infraestructura

### 🟡 Sincronización automática GitHub al agregar norma
**Qué:** Al agregar una nueva fuente y generar sus embeddings, ejecutar `PUSH_GIT.bat` automáticamente.
**Beneficio:** La versión cloud (Streamlit) siempre actualizada.
**Esfuerzo:** Bajo

### 🟢 Tests de regresión para el motor de búsqueda
**Qué:** Set de 20-30 preguntas con respuestas esperadas. Ejecutar antes de cada deploy para detectar regresiones.
**Beneficio:** Detectar si un cambio de configuración rompe el sistema.
**Esfuerzo:** Medio (crear dataset de referencia es lo difícil)

---

## Historial de Mejoras Implementadas

| Fecha | Mejora |
|---|---|
| 23-Feb-2026 | Chunks enriquecidos con etiqueta de norma + limpieza markdown |
| 23-Feb-2026 | `--fuentes` en Puerta de Ingreso CLI (filtro de fuentes por agentes IA) |
| 23-Feb-2026 | Sidebar simplificado: checkboxes por fuente + Recargar Motor |
| 23-Feb-2026 | Prompt único experto legal general (contrataciones, civil, penal, admin) |
| 23-Feb-2026 | Cache de consultas 7 días (04_LOGS/query_cache.json) |
| 23-Feb-2026 | Expansión de query por aspectos distintos (2 variaciones, deepseek-chat) |
| 23-Feb-2026 | chunks.json auto-save en primera carga (cargas futuras instantáneas) |
| 23-Feb-2026 | Rerank top_n=12 (antes 7) |
| 19-Feb-2026 | Fix carga de fuentes en Cloud: rutas relativas, fix widget data_editor |
| 18-Feb-2026 | Motor IA cambiado a DeepSeek R1 (Reasoner) |
| 11-Feb-2026 | Lanzamiento inicial: Hub RAG Monolítico |
