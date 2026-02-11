# MEMORIA: PIPELINE RAG OBLIGATORIO
**Código: RAG-MEM-001**

## FLUJO OBLIGATORIO PARA RAG ESCALABLE

### 1. ARQUITECTURA PIPELINE
```
PDF → Extractor → JSON_lineal → Processor → JSON_procesado → Embedder → Vector_DB → Query_System
```

### 2. PASOS OBLIGATORIOS (NO SALTAR NINGUNO)
1. **Extracción:** PDF → JSON lineal (texto bruto)
2. **Procesamiento:** JSON lineal → JSON estructurado con:
   - Chunking semántico
   - Metadatos (fecha, tipo, autor, temas)
   - Estructura jerárquica
3. **Embeddings Híbridos:** 
   - **Primarios:** Chunks de JSON procesado (búsqueda)
   - **Referencia:** Link a JSON lineal (detalle completo)
4. **Indexado:** Vector DB unificado con metadatos + referencias
5. **Sistema consulta:** Búsqueda rápida → Detalle bajo demanda

### 3. ARQUITECTURA HÍBRIDA (DOBLE NIVEL)
- **Nivel 1 - Búsqueda:** Embeddings de JSONs procesados (resúmenes, conclusiones)
- **Nivel 2 - Detalle:** Referencia a JSONs lineales (texto completo)
- **Flujo:** Pregunta → Embeddings → Documentos relevantes → Texto completo

### 4. PRINCIPIOS FUNDAMENTALES
- ✅ **Automático:** Una vez configurado, procesa miles sin intervención
- ✅ **Escalable:** Funciona con 20 o 20,000 documentos
- ✅ **Reproducible:** Mismos resultados cada vez
- ✅ **Mantenible:** Fácil actualización y corrección

### 4. ERRORES A EVITAR
- ❌ Saltar el JSON lineal
- ❌ Usar embeddings sobre texto bruto
- ❌ Índices fragmentados por documento
- ❌ Procesar manualmente documento por documento

### 5. ESTADO ACTUAL PROYECTO
- **Ubicación:** `C:\Users\juan.montenegro\Desktop\01_BASE_NORMATIVA\006_Opiniones\Opiniones_2025_OECE`
- **Avance:** Pipeline completado para los 20 documentos (20/20). El índice de embeddings está unificado y listo.
- **Pendiente:** Probar el sistema de consultas (Query_System).

### 6. RECORDATORIO OBLIGATORIO
**SIEMPRE** que Juan mencione RAG, recordar este pipeline y NO generar código hasta confirmar estructura completa.