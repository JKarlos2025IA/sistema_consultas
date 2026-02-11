import streamlit as st
from motor_busqueda import QueryRouter
import json
from datetime import datetime
import os
from collections import defaultdict
import requests

# --- Configuración DeepSeek ---
DEEPSEEK_API_KEY = "sk-4e6b4c12e3e24d5c8296b6084aac4aac"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPT = """Eres un experto en contrataciones del Estado peruano, especializado en la Ley 32069 (nueva ley) y la Ley 30225 (anterior ley).

Tu trabajo es responder consultas legales basándote ÚNICAMENTE en las opiniones OECE/OSCE que te proporciono como contexto.

REGLAS ESTRICTAS:
1. Responde SOLO con información del contexto proporcionado
2. SIEMPRE cita el número de opinión y fecha como fuente
3. Busca primero las CONCLUSIONES de las opiniones - ahí está la respuesta directa
4. Si la opinión dice que algo NO procede o NO es aplicable, dilo claramente
5. Diferencia entre la anterior normativa (Ley 30225) y la nueva (Ley 32069)
6. Si no encuentras información relevante, dilo claramente

ESTRUCTURA DE RESPUESTA:
- **Respuesta Directa:** (Sí/No/Depende + explicación breve)
- **Fundamento:** (Cita de la opinión relevante)
- **Conclusión de la Opinión:** (Transcribir la conclusión oficial)

CONTEXTO DE DOCUMENTOS:
{contexto}

---
CONSULTA DEL USUARIO:
{consulta}
"""

def consultar_deepseek(consulta, contexto_chunks):
    """Envía consulta a DeepSeek con el contexto de los documentos encontrados"""
    # Formatear contexto
    contexto = "\n\n".join([
        f"[{i+1}] Opinión: {c['metadata'].get('numero_opinion', 'N/A')} | Fecha: {c['metadata'].get('fecha', 'N/A')} | Asunto: {c['metadata'].get('asunto', 'N/A')}\n{c['chunk_text']}"
        for i, c in enumerate(contexto_chunks)
    ])

    prompt_completo = SYSTEM_PROMPT.format(contexto=contexto, consulta=consulta)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt_completo}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error al consultar DeepSeek: {str(e)}"

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Consulta Normativa Unificada",
    page_icon="⚖️",
    layout="wide"
)

# --- Carga y Cacheo del Modelo ---
@st.cache_resource
def load_query_router():
    router = QueryRouter()
    return router

# --- Inicialización del Estado de la Sesión ---
if 'latest_query' not in st.session_state:
    st.session_state.latest_query = ""
if 'latest_results' not in st.session_state:
    st.session_state.latest_results = None
if 'ia_response' not in st.session_state:
    st.session_state.ia_response = None

# --- Cargar Componentes Principales ---
query_router = load_query_router()
if query_router:
    available_indices = sorted(list(query_router.indices.keys()))
else:
    available_indices = []

# --- Lógica de la Barra Lateral (Sidebar) ---
st.sidebar.title("Filtro de Fuentes")
st.sidebar.markdown("Selecciona las bases de conocimiento. Si no eliges ninguna, se buscará en todas.")

# Agrupar índices por prefijo (ej: "Opiniones")
grouped_indices = defaultdict(list)
for name in available_indices:
    parts = name.split()
    prefix = parts[0] if parts else name
    grouped_indices[prefix].append(name)

# Crear los checkboxes jerárquicos
selected_sources = []
for prefix, names in grouped_indices.items():
    st.sidebar.markdown("---")
    select_all = st.sidebar.checkbox(f"**Todas las {prefix}**", key=f"select_all_{prefix}")
    
    for name in names:
        if select_all:
            selected_sources.append(name)
            st.sidebar.checkbox(name, key=f"checkbox_{name}", value=True, disabled=True)
        else:
            if st.sidebar.checkbox(name, key=f"checkbox_{name}"):
                selected_sources.append(name)

# Eliminar duplicados
selected_sources = sorted(list(set(selected_sources)))

sources_to_search = selected_sources if selected_sources else None

st.sidebar.markdown("---")
st.sidebar.title("Acerca de")
st.sidebar.info(
    "Sistema RAG con IA para consultar la base normativa de contrataciones del Estado."
    "\n\n"
    "**Buscar:** Solo muestra documentos relevantes."
    "\n"
    "**Consultar con IA:** Busca + genera respuesta fundamentada."
    "\n\n"
    "**Fase Actual:** 2.0 - Integración con DeepSeek IA."
)

if query_router and query_router.indices:
    st.sidebar.success(f"Índices cargados: {len(available_indices)}")
else:
    st.sidebar.error("No se pudo cargar ningún índice. Revisa la configuración.")


# --- Interfaz Principal ---
st.title("⚖️ Sistema de Consulta Unificado - Base Normativa")
st.markdown("Escribe tu consulta, selecciona las fuentes en la barra lateral y presiona buscar.")

query_text = st.text_input(
    "Escribe tu consulta:",
    placeholder="Ej: responsabilidad del pago en compras corporativas"
)

# Botones de acción
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    buscar_normal = st.button("Buscar", type="secondary", use_container_width=True)

with col_btn2:
    buscar_ia = st.button("Consultar con IA", type="primary", use_container_width=True)

# Búsqueda normal
if buscar_normal:
    if query_text:
        st.session_state.latest_query = query_text
        st.session_state.ia_response = None
        with st.spinner("Buscando en la base de conocimiento..."):
            results = query_router.search(query_text, top_k=5, sources=sources_to_search)
            st.session_state.latest_results = results
    else:
        st.error("Por favor, introduce una consulta para buscar.")
        st.session_state.latest_results = None

# Búsqueda con IA
if buscar_ia:
    if query_text:
        st.session_state.latest_query = query_text
        with st.spinner("Buscando documentos relevantes..."):
            results = query_router.search(query_text, top_k=15, sources=sources_to_search)
            st.session_state.latest_results = results

        if results:
            with st.spinner("Consultando a la IA con el contexto encontrado..."):
                respuesta = consultar_deepseek(query_text, results)
                st.session_state.ia_response = respuesta
        else:
            st.warning("No se encontraron documentos relevantes para tu consulta.")
            st.session_state.ia_response = None
    else:
        st.error("Por favor, introduce una consulta para buscar.")
        st.session_state.latest_results = None
        st.session_state.ia_response = None

# --- Mostrar Respuesta de IA ---
if st.session_state.ia_response:
    st.subheader("Respuesta de la IA")
    st.markdown(st.session_state.ia_response)
    st.markdown("---")

# --- Mostrar Resultados y Botón de Guardar ---
if st.session_state.latest_results:
    st.subheader("Resultados de la Búsqueda")
    results = st.session_state.latest_results
    
    for i, res in enumerate(results):
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.metric(label="Relevancia", value=f"{res['score']:.4f}")
            st.info(f"**Fuente:**\n{res['source']}")
        
        with col2:
            st.markdown(f"**Texto del Documento:**")
            st.markdown(f"> {res['chunk_text']}")
            
            with st.expander("Ver metadatos del chunk"):
                st.json(res['metadata'])

    st.markdown("---")
    st.subheader("Exportar Resultados")
    if st.button("Guardar Resultados en JSON"):
        results_to_save = []
        for res in st.session_state.latest_results:
            serializable_res = res.copy()
            serializable_res['score'] = float(res['score'])
            results_to_save.append(serializable_res)

        output_data = {
            "query": st.session_state.latest_query,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "sources_searched": sources_to_search if sources_to_search else list(query_router.indices.keys()),
            "ia_response": st.session_state.ia_response if st.session_state.ia_response else None,
            "results": results_to_save
        }
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"consulta_{timestamp_str}.json"
        save_path = os.path.join("../04_LOGS/historial_consultas", file_name)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
            st.success(f"Resultados guardados exitosamente en: `{save_path}`")
        except Exception as e:
            st.error(f"Error al guardar el archivo: {e}")