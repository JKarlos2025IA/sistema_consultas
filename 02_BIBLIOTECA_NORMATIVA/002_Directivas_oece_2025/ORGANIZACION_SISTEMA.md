# ESTRUCTURA DEL PROYECTO - DIRECTIVAS OECE RAG

## DESCRIPCIÓN GENERAL

Este proyecto contiene un sistema RAG específico para las Directivas del Organismo Especializado para las Contrataciones Públicas Eficientes (OECE). A diferencia del sistema general de consultas en la carpeta `000_CONSULTAS`, este es un sistema independiente con embeddings específicos para directivas.

## JUSTIFICACIÓN DE LA ESTRUCTURA

### ¿Por qué archivos .bat en esta carpeta y no en 000_CONSULTAS?

**Razón principal:** Este es un **sistema RAG independiente** con:

1. **Documentos específicos**: Directivas OECE (no el conjunto general de documentos legales)
2. **Embeddings específicos**: Generados solo para las directivas
3. **Configuración específica**: Adaptada a las características de los documentos de directivas
4. **Interfaz específica**: Optimizada para consultas sobre directivas
5. **Rutas relativas específicas**: Apuntan a los archivos de embeddings de directivas

### Diferencias con el sistema general en 000_CONSULTAS:

| Aspecto | Sistema General (000_CONSULTAS) | Sistema Directivas OECE |
|---------|----------------------------------|--------------------------|
| Documentos | Conjunto general de documentos legales | Solo directivas OECE |
| Embeddings | Múltiples fuentes combinadas | Solo directivas OECE |
| Configuración | General para múltiples tipos | Específica para directivas |
| Interfaz | General | Optimizada para directivas |
| Scripts inicio | En su propia carpeta | Específicos para este proyecto |

## ESTRUCTURA DE CARPETAS

```
G:\Mi unidad\01_BASE_NORMATIVA\002_Directivas_oece_2025\
├── 03_TXT_CONVERTIDOS\          # Archivos OCR originales
├── Procesados_Parser_Directivas\ # Archivos JSON estructurados
├── Embeddings_Directivas\       # Archivos de embeddings intermedios
├── embeddings_unificados\       # Archivos de embeddings finales
├── app\                        # Aplicación Streamlit
├── deploy_cloud\               # Scripts para despliegue en la nube
├── scripts\                    # Scripts auxiliares (vieja estructura)
├── SCRIPTS\                    # Scripts de limpieza y procesamiento (nueva estructura)
├── Directiva N° *.pdf          # Archivos PDF originales
├── INICIAR_SERVIDOR.bat        # Inicio del sistema RAG directivas
├── SUBIR_A_GITHUB.bat          # Subida al repositorio
├── config_directivas.json      # Configuración del sistema
├── requirements.txt            # Dependencias
└── README.md                  # Documentación
```

## ARCHIVOS PRINCIPALES

### Scripts de inicio
- `INICIAR_SERVIDOR.bat`: Inicia la aplicación Streamlit localmente
- `SUBIR_A_GITHUB.bat`: Prepara y sube el proyecto a GitHub

### Aplicación
- `app/app_directivas_oece.py`: Interfaz Streamlit principal
- `app/iniciar_remoto.py`: Inicio con acceso remoto via ngrok

### Configuración
- `config_directivas.json`: Configuración específica del sistema
- `requirements.txt`: Dependencias del proyecto

### Datos
- `embeddings_unificados/`: Archivos de embeddings finales
  - `directivas_oece_2025_2026.index`: Índice FAISS
  - `chunks.json`: Fragmentos de texto
  - `metadata.pkl`: Metadatos de los fragmentos

## USO DEL SISTEMA

### Para iniciar localmente:
```
INICIAR_SERVIDOR.bat
```

### Para subir a GitHub:
```
SUBIR_A_GITHUB.bat
```

### Para usar programáticamente:
```python
# El sistema está configurado para usar los embeddings en embeddings_unificados/
# con el modelo especificado en config_directivas.json
```

## NOTA IMPORTANTE

Este sistema es **independiente** del sistema general en `000_CONSULTAS`. Si se desea integrar ambos sistemas, se requiere una modificación específica del archivo de configuración en el sistema general para incluir esta fuente adicional.

## AUTOR

Asistente de IA - Proyecto de automatización de procesamiento legal

---
Documento generado como parte del proceso de organización del sistema RAG para Directivas OECE.