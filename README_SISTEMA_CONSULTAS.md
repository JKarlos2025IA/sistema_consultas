# ⚖️ SISTEMA DE CONSULTA NORMATIVA UNIFICADA (HUB RAG)

> **Documento Maestro de Arquitectura y Operación**
> **Última Actualización:** 23 de Febrero 2026
> **Estado:** Producción (Local + Cloud)
> **Acceso Web:** [sistemaconsultas-2026.streamlit.app](https://sistemaconsultas-2026.streamlit.app/)

## 🎯 Objetivo
Plataforma centralizada ("Hub") que permite buscar y consultar con IA sobre múltiples bases normativas dispersas (Opiniones, Leyes, Directivas). A diferencia de sistemas monolíticos, este sistema actúa como un **conector** de diversas fuentes de conocimiento.

---

## 🔐 Credenciales de Acceso
El sistema está protegido por login simple:
*   **Usuario:** `admin`
*   **Clave:** `consultas2026`

---

## 📂 Arquitectura de Directorios (Modelo Monolítico)

La estructura "Single Source of Truth" en `G:\Mi unidad\01_BASE_NORMATIVA\000_CONSULTAS` es:

| Directorio | Contenido | Función |
| :--- | :--- | :--- |
| `00_START.bat` | Script | Lanzador universal para PC Local. |
| `01_APP_CORE` | 🐍 Python | **Cerebro del sistema**: Interfaz Streamlit y Motor de Búsqueda Híbrido. |
| `02_BIBLIOTECA_NORMATIVA` | 📚 Datos | **Almacén de Normas**: Contiene carpetas independientes (Opiniones, Leyes) con sus PDFs y Embeddings. |
| `03_CONFIG` | ⚙️ Config | Archivo `config.json` que conecta el cerebro con los datos. |
| `04_LOGS` | 🗄️ Historial | Registro de consultas realizadas en JSON. |
| `05_DOCS` | 📄 Docs | Manuales y planes de implementación. |
| `06_SCRIPTS` | 🛠️ Tools | Scripts de mantenimiento y verificación. |

---

## 📂 Gestión de Fuentes (Admin) - Actualizado 23-Feb-2026

### 1. Sidebar — Flujo simplificado

#### 🔍 Consultar en (sección principal)
Muestra **todas** las fuentes configuradas con un checkbox cada una:
- ✅ `Nombre (X vec.)` = cargada en memoria, lista para buscar
- ⚪ `Nombre (no cargada)` = configurada pero inactiva

**Cómo usar:**
1. Marca/desmarca las fuentes que quieres usar
2. Pulsa **🔄 Recargar Motor** para aplicar cambios
3. Escribe tu consulta — el sistema buscará solo en las fuentes marcadas y cargadas

#### ⚙️ Gestión de Fuentes (expander colapsado)
Solo para mantenimiento:
- **Agregar fuente:** Alias + ruta de embeddings → Guardar (aparece automáticamente en los checkboxes)
- **Eliminar fuente:** Seleccionar alias + clave `admin2026`

### 2. Agregar Nueva Norma — Flujo completo
1. Generar embeddings → crea `faiss.index` + `metadata.pkl`
2. En "Gestión de Fuentes": poner Alias + Ruta → Guardar
3. La fuente aparece automáticamente en los checkboxes con ✅
4. Primera carga: el sistema genera `chunks.json` automáticamente (cargas futuras instantáneas)

> **Nota sobre rutas:** El sistema convierte automáticamente rutas absolutas (`G:\Mi unidad\...`) a relativas para compatibilidad Local + Streamlit Cloud.

---

## 🚀 Flujo de Trabajo (Pipeline)

### 1. Ingesta de Nuevas Normas
Para agregar una nueva normativa (ej: "Nueva Ley X"):
1.  Crear carpeta en `02_BIBLIOTECA_NORMATIVA/Nueva_Ley_X`.
2.  Generar embeddings (usando scripts estándar) dentro de esa carpeta (subcarpeta `embeddings_unificados`).
3.  Desde la interfaz, usar **"➕ Agregar Nueva Fuente"** (se registra automáticamente en `03_CONFIG/fuentes_usuario.json`).

### 2. Motor de Búsqueda (`01_APP_CORE/motor_busqueda.py`)
El sistema usa una estrategia **Híbrida + Expansión**:
*   **Reformulación:** DeepSeek-chat corrige typos y expande abreviaciones legales.
*   **Expansión de query:** genera 2 sub-consultas con aspectos distintos para mayor cobertura.
*   **Búsqueda Vectorial (FAISS):** top_k=20 por fuente activa.
*   **Búsqueda Keyword:** refuerza coincidencias exactas de términos legales.
*   **Re-ranking:** cosine similarity real selecciona los 12 mejores chunks.
*   **Cache:** respuestas guardadas en `04_LOGS/query_cache.json` (expira 7 días).
*   **IA (DeepSeek R1 Reasoner):** genera respuesta con Chain of Thought citando fuentes.

### 3. Consumo (Interfaz)
*   **Local:** Ejecutar `00_START.bat`.
*   **Nube:** Acceder vía Streamlit Cloud. Sincronizado vía GitHub.

---

## ☁️ Despliegue a Producción (GitHub) y Estrategia de Almacenamiento

El sistema utiliza una **Estrategia Híbrida de Almacenamiento Inteligente** para optimizar el rendimiento y cumplir con los límites de GitHub.

### 🧠 ¿Qué se sube a la Nube (GitHub/Streamlit)?
Solo la **"Inteligencia"** del sistema.
- **Archivos permitidos:** `.index` (FAISS), `.json` (Metadatos), `.pkl`, `.py` (Código fuente).
- **Objetivo:** Permitir que la IA en la nube (Streamlit) tenga acceso a los "mapas mentales" de los documentos sin necesitar los archivos físicos pesados.
- **Peso típico:** Unos pocos MBs, incluso para bibliotecas de cientos de documentos.

### 🔒 ¿Qué se queda en Local (Google Drive)?
Los **"Documentos Pesados"** y datos sensibles.
- **Archivos bloqueados (`.gitignore`):** `*.pdf`, `*.docx`, `*.zip`, `*.rar`.
- **Ubicación:** Permanecen seguros en `G:\Mi unidad\01_BASE_NORMATIVA\...` y no tocan los servidores públicos de GitHub.
- **Beneficio:** Privacidad total de los textos originales y cero consumo del límite de 2GB de GitHub.

### 🔄 Sincronización Automática
Para actualizar la web, utilice el script `PUSH_GIT.bat` incluido en la raíz. Este script:
1.  Sincroniza con GitHub (`git pull --rebase`) para evitar conflictos con cambios remotos.
2.  Detecta cambios en código o nuevos índices vectoriales.
3.  Ignora automáticamente los PDFs nuevos.
4.  Sube la actualización a GitHub en segundos.

Repositorio: `https://github.com/JKarlos2025IA/sistema_consultas`

**Comandos manuales (si no usa el .bat):**
```bash
# En la carpeta 000_CONSULTAS
git pull --rebase origin main
git add .
git commit -m "Descripción del cambio"
git push origin main
```
*Si agregas una norma nueva a `02_BIBLIOTECA...`, asegúrate de que no tenga carpetas `.git` ocultas dentro.*

---

## 🔌 Acceso Externo (API CLI)

Este Hub Normativo puede ser consultado por agentes de IA mediante la "Puerta de Ingreso":

*   **Script:** `G:\Mi unidad\03_PROJECTS\0003_Scprits\Puerta_ingreso_consultor_ia.py`
*   **Comando:**
    ```bash
    python Puerta_ingreso_consultor_ia.py --sistema consultas --consulta "concepto juridico"
    ```
*   **Uso:** Permite auditar expedientes externos verificando si cumplen con la normativa indexada aquí.

---

## 🛠️ Tecnologías
*   **Frontend:** Streamlit
*   **Vectores:** FAISS + SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`)
*   **Razonamiento:** **DeepSeek R1 (Reasoner)** 🧠
    *   *Modelo actualizado a Feb 2026.*
    *   Usa "Chain of Thought" (Cadena de Pensamiento) para deducir respuestas legales complejas antes de responder.
*   **Lenguaje:** Python 3.10+

---

## 📋 Historial de Cambios

| Fecha | Cambio |
| :--- | :--- |
| 23-Feb-2026 | Sidebar simplificado: checkboxes por fuente + Recargar Motor |
| 23-Feb-2026 | Prompt único experto legal general (contrataciones, civil, penal, admin) |
| 23-Feb-2026 | chunks.json auto-save en primera carga (cargas futuras instantáneas) |
| 23-Feb-2026 | Cache de consultas (04_LOGS/query_cache.json, 7 días, 200 entradas max) |
| 23-Feb-2026 | Expansión de query por aspectos distintos (deepseek-chat, 2 variaciones) |
| 23-Feb-2026 | Rerank top_n 7→12 para preguntas de proceso amplio |
| 23-Feb-2026 | PUSH_GIT.bat: fix orden (add→commit→pull→push) |
| 19-Feb-2026 | Fix carga de fuentes en Cloud: rutas relativas, fix widget data_editor |
| 19-Feb-2026 | PUSH_GIT.bat con `git pull --rebase`, eliminado `.devcontainer/` |
| 18-Feb-2026 | Motor IA cambiado a DeepSeek R1 (Reasoner), Borrado Nuclear de fuentes |
| 11-Feb-2026 | Lanzamiento inicial: Hub RAG Monolítico con gestión dinámica de fuentes |
