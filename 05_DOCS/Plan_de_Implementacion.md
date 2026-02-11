# Plan de Implementación y Visión Estratégica
## Sistema de Consulta Normativa Unificada

---

### **Ficha del Paciente**

*   **Nombre del Proyecto:** Sistema de Consulta Normativa Unificada
*   **Fecha de Evaluación:** 26 de noviembre de 2025
*   **Médico a Cargo:** Asistente Gemini

---

### **1. Visión (El Futuro Deseado)**

Convertir este sistema en el **cerebro central y única fuente de verdad** para toda la inteligencia normativa de la organización. Aspiramos a que no solo sea un buscador, sino un **asistente experto proactivo** que entienda el contexto legal, resuma información compleja y ofrezca respuestas precisas y fundamentadas, accesible desde cualquier lugar y en cualquier momento.

---

### **2. Misión (El Propósito Actual)**

La misión del sistema es **centralizar y democratizar el acceso a la base de conocimiento normativo**. Lo logra a través de una interfaz de búsqueda unificada que consulta, de manera modular y escalable, múltiples bases de datos vectoriales (índices) que representan diferentes conjuntos de documentos (leyes, opiniones, etc.).

---

### **3. Diagnóstico (Estado y Estructura Actual)**

El sistema es una **aplicación de Búsqueda y Generación Aumentada (RAG) funcional y robusta**, con una arquitectura bien diseñada que fomenta la escalabilidad.

*   **Tipo:** Aplicación Web Local.
*   **Tecnología Principal:**
    *   **Backend:** Python.
    *   **Interfaz de Usuario:** Streamlit.
    *   **Búsqueda por IA:** `sentence-transformers` para la comprensión del lenguaje y `faiss-cpu` para la búsqueda vectorial de alta velocidad.
*   **Arquitectura de Datos:**
    *   **Modular:** El sistema utiliza un "Enrutador de Consultas" que lee un archivo `config.json` para localizar y buscar en múltiples índices de vectores de forma independiente.
    *   **Escalable:** Añadir nuevas fuentes de conocimiento solo requiere (1) procesar los documentos en un nuevo índice y (2) añadir su ruta al `config.json`, sin necesidad de alterar el código.
*   **Estado de Salud Actual (Refactorización del 26/11/2025):**
    *   **Portable:** Se ha eliminado la dependencia de rutas absolutas. El proyecto ahora utiliza **rutas relativas**, lo que lo hace autocontenido y portable.
    *   **Distribuible:** Se ha creado un archivo **`requirements.txt`**, permitiendo que el entorno de la aplicación sea replicado fácilmente en cualquier máquina.

**Conclusión del Diagnóstico:** El paciente goza de buena salud estructural. Ha superado con éxito la fase de prototipo local y está en condiciones óptimas para ser llevado a un entorno de producción (la web).

---

### **4. Plan de Tratamiento (Mejoras Pendientes a Implementar)**

Se recomienda el siguiente plan de tratamiento, dividido en fases, para alcanzar la visión a largo plazo.

#### **Fase 1: Despliegue y Accesibilidad Global (Inmediato)**

1.  **Control de Versiones:**
    *   **Acción:** Inicializar un repositorio de **Git** y subir el proyecto completo a **GitHub**.
    *   **Objetivo:** Tener un historial de cambios, facilitar la colaboración y habilitar el despliegue automático.
2.  **Puesta en Producción:**
    *   **Acción:** Conectar el repositorio de GitHub a **Streamlit Community Cloud**.
    *   **Objetivo:** Publicar la aplicación en una URL pública y gratuita, haciéndola accesible desde cualquier lugar.

#### **Fase 2: Mejora de la Experiencia de Usuario (Corto Plazo)**

1.  **Filtros Avanzados:**
    *   **Acción:** Modificar la interfaz para leer los `metadata.pkl` y permitir filtrar no solo por fuente, sino también por **año, tipo de documento, número de resolución**, etc.
    *   **Objetivo:** Dar al usuario un control mucho más granular sobre el alcance de sus búsquedas.
2.  **Gestión de Resultados:**
    *   **Acción:** Implementar **paginación** en la interfaz para manejar un gran número de resultados de forma ordenada.
    *   **Objetivo:** Mejorar la legibilidad y el rendimiento cuando las búsquedas devuelven muchas coincidencias.

#### **Fase 3: Evolución a Asistente de IA (Mediano Plazo)**

1.  **Integración de un LLM:**
    *   **Acción:** Conectar la salida del buscador a una API de un modelo de lenguaje grande (como **Gemini**).
    *   **Objetivo:** Transformar el sistema de un "buscador" a un "respondedor". La IA leerá los textos encontrados y generará una **respuesta directa, resumida y en lenguaje natural**, citando las fuentes que utilizó.
2.  **Memoria Conversacional:**
    *   **Acción:** Implementar una función para que el sistema "recuerde" las preguntas anteriores en una misma sesión.
    *   **Objetivo:** Permitir búsquedas de seguimiento y un diálogo más natural con el asistente.

#### **Fase 4: Industrialización y Mantenimiento (Largo Plazo)**

1.  **Automatización del Pipeline RAG:**
    *   **Acción:** Crear scripts para **automatizar la creación de nuevos índices** a partir de una carpeta de documentos.
    *   **Objetivo:** Reducir la fricción y el trabajo manual para añadir nuevas bases de conocimiento al sistema.
2.  **Logging y Monitoreo:**
    *   **Acción:** Implementar un sistema de logging más avanzado para registrar las búsquedas realizadas, los resultados obtenidos y los posibles errores.
    *   **Objetivo:** Obtener métricas sobre el uso del sistema e identificar áreas de mejora.
