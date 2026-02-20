# ⚖️ SISTEMA DE CONSULTA NORMATIVA UNIFICADA (HUB RAG)

> **Documento Maestro de Arquitectura y Operación**
> **Última Actualización:** 19 de Febrero 2026
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

## 📂 Gestión de Fuentes (Admin) - NUEVO (Feb 2026)

El sistema cuenta con un panel de control avanzado en la barra lateral para gestionar qué normativas se consultan en tiempo real.

### 1. Panel de Control "En Vivo"
*   **Columna "Cargar":** Checkbox para activar/desactivar una fuente. Marca solo las fuentes que necesitas consultar.
*   **Botón "🔄 Cargar / Actualizar Motor":** Después de cambiar los checkboxes, pulsa este botón para aplicar los cambios. El motor se recargará solo con las fuentes marcadas.
*   **Columna "Estado":**
    *   ✅ **Listo:** La fuente está cargada en memoria y lista para responder.
    *   ⚪ **Inactivo:** La fuente está en tu lista pero NO se está usando actualmente.

### 2. Agregar Nuevas Normas
Desde el desplegable **"➕ Agregar Nueva Fuente"**:
1.  Pon un **Alias** (nombre corto).
2.  Pega la **Ruta de Embeddings** (debe ser la carpeta que contiene `embeddings_unificados`).
3.  Pulsa **Guardar**.

### 3. Eliminación Segura ("Borrado Nuclear")
Para eliminar una fuente de la lista:
1.  Borra la fila correspondiente en la tabla.
2.  Aparecerá un aviso de confirmación.
3.  Ingresa la **Clave Maestra de Borrado**: `admin2026`.
4.  Al confirmar, el sistema ejecuta un **Borrado Nuclear**:
    *   Elimina la fuente del archivo de configuración.
    *   Purga la memoria Caché del servidor.
    *   Recarga el sistema desde cero para evitar "zombies".

---

## 🚀 Flujo de Trabajo (Pipeline)

### 1. Ingesta de Nuevas Normas
Para agregar una nueva normativa (ej: "Nueva Ley X"):
1.  Crear carpeta en `02_BIBLIOTECA_NORMATIVA/Nueva_Ley_X`.
2.  Generar embeddings (usando scripts estándar) dentro de esa carpeta (subcarpeta `embeddings_unificados`).
3.  Registrar la nueva ruta en `03_CONFIG/config.json`.

### 2. Motor de Búsqueda (`01_APP_CORE/motor_busqueda.py`)
El sistema usa una estrategia **Híbrida**:
*   **Búsqueda Vectorial (FAISS):** Encuentra conceptos semánticos.
*   **Búsqueda Keyword:** Refuerza coincidencias exactas.
*   **IA (DeepSeek):** Genera respuestas fundamentadas citando la fuente.

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
