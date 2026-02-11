# Sistema RAG para Directivas OECE

Sistema de Recuperación Aumentada por Generación (RAG) para consultar las Directivas del Organismo Especializado para las Contrataciones Públicas Eficientes (OECE).

## Descripción

Este sistema permite realizar búsquedas semánticas sobre las directivas emitidas por la OECE, facilitando el acceso rápido a información normativa relevante para las contrataciones públicas eficientes.

## Características

- Búsqueda semántica sobre documentos legales
- Interfaz web intuitiva con autenticación
- Acceso remoto seguro
- Integración con modelos de lenguaje avanzados
- Sistema de autenticación

## Tecnologías

- Python 3.12+
- Streamlit
- FAISS
- Sentence Transformers
- DeepSeek API (o modelo local alternativo)

## Estructura del Proyecto

```
directivas-oece-rag/
├── app/
│   ├── app_directivas_oece.py
│   └── iniciar_remoto.py
├── embeddings_unificados/          # (NO SUBIDO A GITHUB - DEMASIADO GRANDE)
│   ├── directivas_oece_2025_2026.index   # Archivo binario ~918KB
│   ├── chunks.json                   # Archivo de texto ~590KB  
│   └── metadata.pkl                  # Archivo binario ~21KB
├── deploy_cloud/
├── scripts/
├── SCRIPTS/                         # Scripts de limpieza y procesamiento
├── config_directivas.json
├── INICIAR_SERVIDOR.bat
├── requirements.txt
└── README.md
```

## IMPORTANTE: Archivos de Embeddings

Debido a los límites de GitHub (100MB por archivo), **los archivos de embeddings no se suben directamente al repositorio**. Estos archivos son:

- `directivas_oece_2025_2026.index` (~918KB) - Índice FAISS
- `chunks.json` (~590KB) - Fragmentos de texto
- `metadata.pkl` (~21KB) - Metadatos

## Instalación y Uso

### Opción 1: Si tienes acceso a los archivos de embeddings completos

1. Clonar el repositorio:
```bash
git clone https://github.com/TU_USUARIO/directivas-oece-rag.git
```

2. Descargar los archivos de embeddings por separado (ver sección de descarga más abajo)

3. Colocar los archivos en la carpeta `embeddings_unificados/`

4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

5. Iniciar la aplicación:
```bash
streamlit run app/app_directivas_oece.py
```

### Opción 2: Regenerar embeddings desde documentos originales

1. Clonar el repositorio:
```bash
git clone https://github.com/TU_USUARIO/directivas-oece-rag.git
```

2. Asegurarte de tener los archivos JSON procesados en `Procesados_Parser_Directivas/`

3. Regenerar los archivos de chunks y metadata:
```bash
python scripts/regenerar_embeddings.py
```

4. Nota: Este proceso recrea `chunks.json` y `metadata.pkl`, pero no puede recrear el archivo `.index` sin el modelo completo de embeddings.

## Credenciales de Acceso

- Usuario: `admin` - Clave: `directivas2026`
- Usuario: `abogado` - Clave: `oece2026`
- Usuario: `consultor` - Clave: `contrataciones2026`

## Descarga de Archivos de Embeddings

Los archivos de embeddings pueden descargarse por separado desde:

[ENLACE DE DESCARGA AQUÍ - PENDIENTE CONFIGURACIÓN]

## Despliegue

Para despliegue en producción:
1. Asegurar que los archivos de embeddings estén disponibles
2. Configurar variables de entorno para claves API
3. Ajustar parámetros en `config_directivas.json`
4. Iniciar con `INICIAR_SERVIDOR.bat` o directamente con Streamlit

## Autor

Asistente de IA - Proyecto de automatización de procesamiento legal

## Licencia

[Por definir]

## Notas Importantes

- El sistema está optimizado para documentos legales en español
- La calidad de las respuestas depende de la calidad de los embeddings
- Para aplicaciones críticas, se recomienda revisión humana de los resultados
- El sistema mantiene la integridad del contenido legal original