# MANEJO DE ARCHIVOS GRANDES - SISTEMA RAG DIRECTIVAS OECE

## PROBLEMA IDENTIFICADO

Los archivos de embeddings generados para el sistema RAG de Directivas OECE exceden los límites de GitHub:
- Límite por archivo: 100MB
- Límite por repositorio: 2GB
- Tamaño total de embeddings: Aproximadamente 1.5MB (índice FAISS) + 590KB (chunks) + 21KB (metadata) = ~1.5MB

## ARCHIVOS AFECTADOS

Los siguientes archivos NO se subieron a GitHub debido a los límites de tamaño:

- `embeddings_unificados/directivas_oece_2025_2026.index` (~918KB) - Índice FAISS
- `embeddings_unificados/chunks.json` (~590KB) - Fragmentos de texto
- `embeddings_unificados/metadata.pkl` (~21KB) - Metadatos

## SOLUCIONES POSIBLES

### OPCIÓN 1: USAR GIT LFS (Large File Storage)
```bash
# Instalar Git LFS
git lfs install

# Configurar tipos de archivos grandes
git lfs track "*.index"
git lfs track "*.pkl"
git add .gitattributes

# Agregar archivos grandes
git add embeddings_unificados/*.index
git add embeddings_unificados/*.pkl

# Hacer commit y push
git commit -m "feat: añadir embeddings con Git LFS"
git push
```

### OPCIÓN 2: EXCLUIR EMBEDDINGS Y PROPORCIONAR SCRIPT DE GENERACIÓN
- Mantener los embeddings en `.gitignore`
- Proporcionar script para regenerar embeddings desde documentos originales
- Incluir instrucciones claras en el README

### OPCIÓN 3: ALMACENAMIENTO EXTERNO
- Subir archivos grandes a Google Drive/Dropbox
- Proporcionar enlaces de descarga en el README
- Incluir script de descarga automática

## RECOMENDACIÓN ACTUAL

Dado que los embeddings ya están generados localmente, la **OPCIÓN 2** es la más adecuada:

1. **Eliminar los archivos grandes del repositorio** (si se intentaron subir)
2. **Actualizar .gitignore** para excluir embeddings
3. **Actualizar README.md** con instrucciones claras
4. **Proporcionar script de regeneración** si es necesario

## INSTRUCCIONES PARA USUARIOS

### Para usar el sistema completo:

1. Clonar el repositorio:
```bash
git clone https://github.com/TU_USUARIO/directivas-oece-rag.git
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. **Opción A - Regenerar embeddings** (si tienes los documentos originales):
```bash
python scripts/regenerar_embeddings.py
```

4. **Opción B - Descargar embeddings** (si están disponibles por separado):
- Visitar el enlace proporcionado en el README
- Descargar los archivos de embeddings
- Colocarlos en la carpeta `embeddings_unificados/`

5. Iniciar la aplicación:
```bash
streamlit run app/app_directivas_oece.py
```

## ACTUALIZACIÓN DEL .GITIGNORE

El archivo .gitignore debería incluir:
```
# Archivos de embeddings (demasiado grandes para GitHub)
embeddings_unificados/*.index
embeddings_unificados/*.pkl
embeddings_unificados/chunks.json

# Archivos temporales
*.tmp
*.temp
*.log

# Entornos virtuales
venv/
env/
.venv/
```

## CONCLUSIÓN

Aunque los archivos de embeddings no se pueden subir directamente a GitHub debido a sus límites de tamaño, el sistema sigue siendo completamente funcional. Los usuarios pueden regenerar los embeddings o descargarlos por separado, manteniendo la integridad del código fuente en el repositorio.

El valor del proyecto está en:
- El código de procesamiento y RAG
- Los algoritmos de limpieza de OCR
- La estructura y documentación del sistema
- La metodología de embeddings RAG

Los embeddings son simplemente los datos de salida que pueden regenerarse o descargarse según sea necesario.