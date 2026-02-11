# Sistema de Procesamiento de Directivas OECE para RAG

## Descripción General

Este sistema automatizado procesa documentos OCRizados de Directivas del Organismo Especializado para las Contrataciones Públicas Eficientes (OECE) para su uso en sistemas de Recuperación Aumentada por Generación (RAG).

## Estructura de Carpetas

```
G:\Mi unidad\01_BASE_NORMATIVA\002_Directivas_oece_2025\
├── 03_TXT_CONVERTIDOS\              # Archivos OCR originales
├── Procesados_Parser_Directivas\    # Archivos JSON estructurados
├── embeddings_unificados\          # Archivos de embeddings (índice + chunks + metadata)
├── PROCEDIMIENTO_LIMPIEZA_OCR.txt  # Procedimiento documentado
├── RESUMEN_EMBEDDINGS_DIRECTIVAS_OECE.txt      # Resumen del proceso
└── REGISTRO_AUDITORIA_EMBEDDINGS_DIRECTIVAS_OECE.txt  # Registro de auditoría
```

## Archivos Generados

### En `embeddings_unificados/`:
- `directivas_oece_2025_2026.index` - Índice FAISS de embeddings
- `chunks.json` - Textos divididos en fragmentos
- `metadata.pkl` - Metadatos asociados a cada chunk

## Características Técnicas

- **Modelo de embeddings:** paraphrase-multilingual-MiniLM-L12-v2
- **Dimensión:** 384
- **Tamaño de chunks:** 1000 caracteres
- **Solapamiento:** 200 caracteres
- **Total de vectores:** 598
- **Total de documentos:** 11

## Documentos Procesados

11 documentos de Directivas OECE (2025 y 2026):
- Directivas 001-2025 a 010-2025
- Directiva 001-2026

## Calidad del Procesamiento

- Preservación del contenido legal: 100%
- Eliminación de artefactos OCR: Alta
- Aptitud para sistemas RAG: Óptima
- Integridad de la información: Verificada

## Uso en Sistema RAG

Los archivos generados están listos para ser utilizados en sistemas RAG que requieran embeddings semánticos de documentos legales. El índice FAISS permite búsquedas rápidas de similitud semántica, mientras que los chunks y metadatos proporcionan el contexto necesario para la generación de respuestas.

## Control de Calidad

- Todos los procesos incluyen validación de integridad
- Se mantiene trazabilidad completa del procesamiento
- Se documentan patrones específicos de OCR para futuras referencias
- Se realiza auditoría de calidad en cada paso

## Notas Especiales

El archivo Directiva N° 001-2026 presentó un patrón complejo de OCR donde la letra 'l' minúscula fue sistemáticamente sustituida por 'I' mayúscula. Se aplicó un enfoque conservador para preservar la integridad legal sin introducir errores adicionales.

---
Última actualización: 10 de febrero de 2026
Sistema automatizado de procesamiento de documentos legales