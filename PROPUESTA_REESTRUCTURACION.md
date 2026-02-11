# 🏗️ PROPUESTA DE REESTRUCTURACIÓN: SISTEMA DE CONSULTAS NORMATIVAS

> **Objetivo:** Ordenar el "Hub Central" de Consultas (`000_CONSULTAS`) para que sea escalable, manteniendo su conexión con las carpetas de normas externas.

---

## 1. Diagnóstico Actual

El sistema actual funciona como un **Enrutador Central** (Hub) que conecta con múltiples fuentes de datos dispersas en `G:\Mi unidad\01_BASE_NORMATIVA`.

**Problema:**
La carpeta `000_CONSULTAS` mezcla en la raíz:
- Código fuente (`core_interfaz.py`, `core_motor_busqueda.py`)
- Configuración (`config.json`)
- Documentación (`MANUAL...`)
- Scripts de mantenimiento (`verificar_integracion.py`)
- Logs (`historial_consultas`)

Esto hace difícil saber qué es código crítico y qué es soporte.

---

## 2. Nueva Estructura Propuesta

Se propone organizar el sistema en 5 módulos claros, similar al "Caso Penal" pero adaptado a este modelo descentralizado.

### 📂 Estructura de Carpetas

```text
G:\Mi unidad\01_BASE_NORMATIVA\000_CONSULTAS
│
├── 00_START.bat                     # (Raíz) Lanzador principal (único archivo suelto)
│
├── 01_APP_CORE/                     # CEREBRO DEL SISTEMA
│   ├── app_interfaz.py              # (Antes core_interfaz.py) Frontend Streamlit
│   ├── motor_busqueda.py            # (Antes core_motor_busqueda.py) Backend Search
│   └── utils.py                     # Funciones auxiliares
│
├── 02_CONFIG/                       # CONFIGURACIÓN
│   ├── config.json                  # Mapa de conexiones a carpetas externas
│   └── prompt_templates.json        # (Opcional) Plantillas de respuestas IA
│
├── 03_LOGS/                         # MEMORIA
│   └── historial_consultas/         # Logs de preguntas y respuestas
│
├── 04_DOCS/                         # CONOCIMIENTO
│   ├── MANUAL_SISTEMA.md
│   ├── Plan_Implementacion.md
│   └── README_ARQUITECTURA.md
│
└── 05_SCRIPTS/                      # MANTENIMIENTO
    ├── verificar_conexiones.py      # (Antes verificar_integracion.py)
    └── generar_nuevo_indice.py      # Script ayuda para procesar nuevas normas
```

---

## 3. Flujo de Trabajo (Protocolo de Conexión)

A diferencia del Caso Penal (donde todo está junto), este sistema usa un modelo **Federado**.

### ¿Cómo agregar una nueva norma?

1.  **En la Carpeta de la Norma (Externo):**
    *   Ir a `G:\Mi unidad\01_BASE_NORMATIVA\011_NUEVA_LEY`
    *   Ejecutar script de embeddings local (se debe estandarizar este script).
    *   Generar carpeta `embeddings_unificados` (con `.index`, `.json`, `.pkl`).

2.  **En el Sistema Central (Aquí):**
    *   Editar `02_CONFIG\config.json`.
    *   Agregar la nueva entrada apuntando a la ruta relativa `../011_NUEVA_LEY/...`.
    *   Ejecutar `05_SCRIPTS\verificar_conexiones.py` para confirmar que el Hub "ve" la nueva norma.
    *   Reiniciar `00_START.bat`.

---

## 4. Beneficios

1.  **Limpieza:** La raíz queda limpia, solo con el botón de "START".
2.  **Escalabilidad:** Separar `CONFIG` del código permite actualizar el software sin romper las rutas de las normas.
3.  **Mantenimiento:** Los scripts de prueba están aislados en `05_SCRIPTS`, evitando ejecuciones accidentales.

## 5. Pasos para Ejecutar el Cambio

1.  Crear las carpetas `01_APP_CORE`, `02_CONFIG`, `03_LOGS`, `04_DOCS`, `05_SCRIPTS`.
2.  Mover los archivos a sus nuevos hogares.
3.  **CRÍTICO:** Actualizar las rutas dentro de `motor_busqueda.py` para que encuentre `../02_CONFIG/config.json`.
4.  Actualizar `00_START.bat` para apuntar a `01_APP_CORE\app_interfaz.py`.

¿Procedemos con esta reestructuración?
