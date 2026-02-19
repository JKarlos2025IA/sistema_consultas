import streamlit as st
from motor_busqueda import QueryRouter
import json
from datetime import datetime
import os
from collections import defaultdict
import requests
import pandas as pd

# --- Configuración DeepSeek ---
DEEPSEEK_API_KEY = "sk-4e6b4c12e3e24d5c8296b6084aac4aac"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

DEFAULT_PROMPT = """Eres un asistente legal especializado. Tu trabajo es responder consultas basándote ÚNICAMENTE en los documentos proporcionados como contexto.

REGLAS:
1. Responde SOLO con información del contexto proporcionado.
2. Si la información no es exacta, infiere con cautela citando la fuente.
3. SIEMPRE cita la fuente (documento, artículo, opinión, fecha).
4. Si el contexto es insuficiente, dilo claramente.

ESTRUCTURA DE RESPUESTA:
- **Respuesta Directa:** (Sí/No/Depende + explicación breve)
- **Fundamento:** (Análisis citando los documentos)
- **Referencias:** (Lista de documentos utilizados)"""

PROMPT_TEMPLATE = """{system_prompt}

CONTEXTO DE DOCUMENTOS:
{contexto}

---
CONSULTA DEL USUARIO:
{consulta}
"""

def consultar_deepseek(consulta, contexto_chunks, system_prompt=None):
    """Envía consulta a DeepSeek con el contexto de los documentos encontrados"""
    if system_prompt is None:
        system_prompt = DEFAULT_PROMPT

    contexto = "\n\n".join([
        f"[{i+1}] Fuente: {c['source']} | Título: {c['metadata'].get('titulo', 'N/A')}\n{c['chunk_text']}"
        for i, c in enumerate(contexto_chunks)
    ])

    prompt_completo = PROMPT_TEMPLATE.format(system_prompt=system_prompt, contexto=contexto, consulta=consulta)

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

# --- Gestión de Fuentes de Usuario ---
USER_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../03_CONFIG/fuentes_usuario.json')

def load_user_sources():
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=["activo", "alias", "ruta"])

def save_user_sources(df):
    try:
        data = df.to_dict(orient="records")
        with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error guardando fuentes: {e}")

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Consulta Normativa Unificada",
    page_icon="⚖️",
    layout="wide"
)

# --- Sistema de Login Simple ---
def verificar_login():
    """Verifica credenciales de acceso."""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if st.session_state.autenticado:
        return True

    st.markdown("## 🔐 Acceso al Sistema de Consultas")
    st.markdown("Por favor, ingrese sus credenciales para continuar.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuario = st.text_input("Usuario", key="login_user")
        clave = st.text_input("Clave", type="password", key="login_pass")

        if st.button("Ingresar", use_container_width=True):
            if usuario == "admin" and clave == "consultas2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    return False

if not verificar_login():
    st.stop()

# --- Carga y Cacheo del Modelo ---
@st.cache_resource
def load_query_router():
    router = QueryRouter()
    return router

# --- Gestión de Prompts ---
PROMPTS_PATH = os.path.join(os.path.dirname(__file__), '../03_CONFIG/prompts.json')

def load_prompts():
    if os.path.exists(PROMPTS_PATH):
        try:
            with open(PROMPTS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return [{"nombre": "General Legal", "activo": True, "prompt": DEFAULT_PROMPT}]

def save_prompts(prompts_list):
    try:
        with open(PROMPTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(prompts_list, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error guardando prompts: {e}")

# --- Inicialización del Estado de la Sesión ---
if 'latest_query' not in st.session_state:
    st.session_state.latest_query = ""
if 'latest_results' not in st.session_state:
    st.session_state.latest_results = None
if 'ia_response' not in st.session_state:
    st.session_state.ia_response = None
if 'user_sources_df' not in st.session_state:
    st.session_state.user_sources_df = load_user_sources()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'prompts_list' not in st.session_state:
    st.session_state.prompts_list = load_prompts()

# --- Cargar Componentes Principales ---
query_router = load_query_router()
available_indices = sorted(list(query_router.indices.keys())) if query_router else []

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Configuración")

# 1. Gestión de Fuentes (tabla unificada base + usuario)
st.sidebar.subheader("📂 Gestión de Fuentes")

# Construir tabla unificada
_load_status = getattr(query_router, 'load_status', {})
_filas_unificadas = []

# Indices base (config.json)
for idx_info in query_router.config.get('indices', []):
    nombre = idx_info['nombre']
    status = _load_status.get(nombre, {})
    vec = status.get('vectores', 0) if status.get('estado') == 'ok' else 0
    _filas_unificadas.append({"Cargar": True, "Nombre": nombre, "Vectores": vec, "_tipo": "base"})

# Indices usuario (fuentes_usuario.json)
for _, row in st.session_state.user_sources_df.iterrows():
    alias = row.get('alias', '')
    activo = row.get('activo', True)
    status = _load_status.get(alias, {})
    vec = status.get('vectores', 0) if status.get('estado') == 'ok' else 0
    _filas_unificadas.append({"Cargar": activo, "Nombre": alias, "Vectores": vec, "_tipo": "usuario"})

_df_unificada = pd.DataFrame(_filas_unificadas)

_nombres_originales = set(_df_unificada["Nombre"].tolist())
_user_aliases = st.session_state.user_sources_df['alias'].tolist() if not st.session_state.user_sources_df.empty else []

if not _df_unificada.empty:
    edited_sources = st.sidebar.data_editor(
        _df_unificada[["Cargar", "Nombre", "Vectores"]],
        column_config={
            "Cargar": st.column_config.CheckboxColumn("Cargar", help="Incluir en la búsqueda", default=True),
            "Nombre": st.column_config.TextColumn("Fuente"),
            "Vectores": st.column_config.NumberColumn("Vec.", disabled=True, width="small"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="unified_sources"
    )
    # Determinar qué indices buscar según checkboxes
    sources_to_search = edited_sources[edited_sources["Cargar"] == True]["Nombre"].tolist()

    # Detectar filas eliminadas desde la tabla
    _nombres_editados = set(edited_sources["Nombre"].tolist())
    _eliminados = _nombres_originales - _nombres_editados
    _user_eliminados = [n for n in _eliminados if n in _user_aliases]

    if _user_eliminados:
        st.sidebar.warning(f"Eliminar: {', '.join(_user_eliminados)}")
        _del_pass = st.sidebar.text_input("Clave para confirmar:", type="password", key="del_pass_fuentes")
        _col1, _col2 = st.sidebar.columns(2)
        with _col1:
            if st.button("Confirmar", key="confirm_del_fuente"):
                if _del_pass == "admin2026":
                    for name in _user_eliminados:
                        st.session_state.user_sources_df = st.session_state.user_sources_df[
                            st.session_state.user_sources_df['alias'] != name
                        ].reset_index(drop=True)
                    save_user_sources(st.session_state.user_sources_df)
                    st.sidebar.success("Eliminado.")
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.sidebar.error("Clave incorrecta.")
        with _col2:
            if st.button("Cancelar", key="cancel_del_fuente"):
                st.rerun()
else:
    sources_to_search = available_indices

# Agregar nueva fuente (st.form evita doble registro)
with st.sidebar.expander("➕ Agregar Nueva Fuente", expanded=False):
    with st.form("form_add_source", clear_on_submit=True):
        new_alias = st.text_input("Alias", placeholder="Ej: LEY 27444")
        new_path = st.text_input("Ruta de Embeddings", placeholder="G:\\Mi unidad\\...")
        submitted = st.form_submit_button("Guardar")
        if submitted and new_alias and new_path:
            if not os.path.exists(new_path):
                st.error(f"La ruta no existe: {new_path}")
            else:
                new_row = {"activo": True, "alias": new_alias, "ruta": new_path}
                st.session_state.user_sources_df = pd.concat(
                    [st.session_state.user_sources_df, pd.DataFrame([new_row])],
                    ignore_index=True
                )
                save_user_sources(st.session_state.user_sources_df)
                st.success("Guardado.")
                st.cache_resource.clear()
                st.rerun()

if st.sidebar.button("🔄 Cargar / Actualizar Motor"):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.markdown("---")

# 2. Gestión de Prompts
st.sidebar.subheader("🤖 Prompt de Búsqueda")

# Tabla de prompts con eliminación desde toolbar
_prompts_df = pd.DataFrame([
    {"Activo": p["activo"], "Nombre": p["nombre"]}
    for p in st.session_state.prompts_list
])
_nombres_prompts_orig = set(_prompts_df["Nombre"].tolist())

edited_prompts = st.sidebar.data_editor(
    _prompts_df,
    column_config={
        "Activo": st.column_config.CheckboxColumn("Usar", help="Selecciona el prompt activo", default=False),
        "Nombre": st.column_config.TextColumn("Tema"),
    },
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic",
    key="prompts_editor"
)

# Detectar prompts eliminados desde la tabla
_nombres_prompts_edit = set(edited_prompts["Nombre"].tolist())
_prompts_eliminados = _nombres_prompts_orig - _nombres_prompts_edit

if _prompts_eliminados and len(st.session_state.prompts_list) > 1:
    st.sidebar.warning(f"Eliminar: {', '.join(_prompts_eliminados)}")
    _del_pass_p = st.sidebar.text_input("Clave para confirmar:", type="password", key="del_pass_prompts")
    _col_p1, _col_p2 = st.sidebar.columns(2)
    with _col_p1:
        if st.button("Confirmar", key="confirm_del_prompt"):
            if _del_pass_p == "admin2026":
                st.session_state.prompts_list = [p for p in st.session_state.prompts_list if p["nombre"] not in _prompts_eliminados]
                if not any(p["activo"] for p in st.session_state.prompts_list):
                    st.session_state.prompts_list[0]["activo"] = True
                save_prompts(st.session_state.prompts_list)
                st.sidebar.success("Eliminado.")
                st.rerun()
            else:
                st.sidebar.error("Clave incorrecta.")
    with _col_p2:
        if st.button("Cancelar", key="cancel_del_prompt"):
            st.rerun()

# Detectar cambio de selección y asegurar solo 1 activo
if not _prompts_eliminados:
    _activos = edited_prompts[edited_prompts["Activo"] == True]
    if len(_activos) > 0:
        _nombre_activo = _activos.iloc[-1]["Nombre"]
        for p in st.session_state.prompts_list:
            p["activo"] = (p["nombre"] == _nombre_activo)
    else:
        _nombre_activo = st.session_state.prompts_list[0]["nombre"]
        st.session_state.prompts_list[0]["activo"] = True

# Obtener prompt activo
_prompt_activo = next((p for p in st.session_state.prompts_list if p["activo"]), st.session_state.prompts_list[0])

# Text area editable con el prompt seleccionado
_prompt_editado = st.sidebar.text_area(
    f"Prompt: {_prompt_activo['nombre']}",
    value=_prompt_activo["prompt"],
    height=150,
    help="Edita el prompt. Los cambios se guardan al hacer clic fuera del campo."
)

# Guardar si cambió
if _prompt_editado != _prompt_activo["prompt"]:
    _prompt_activo["prompt"] = _prompt_editado
    save_prompts(st.session_state.prompts_list)

# Agregar nuevo prompt
with st.sidebar.expander("➕ Agregar Prompt", expanded=False):
    with st.form("form_add_prompt", clear_on_submit=True):
        new_prompt_name = st.text_input("Nombre del tema", placeholder="Ej: Derecho Laboral")
        new_prompt_text = st.text_area("Instrucciones", placeholder="Eres un especialista en...", height=100)
        submitted_p = st.form_submit_button("Guardar Prompt")
        if submitted_p and new_prompt_name and new_prompt_text:
            st.session_state.prompts_list.append({
                "nombre": new_prompt_name,
                "activo": False,
                "prompt": new_prompt_text
            })
            save_prompts(st.session_state.prompts_list)
            st.success("Prompt guardado.")
            st.rerun()

st.sidebar.markdown("---")

# 3. Herramientas de Sesión
st.sidebar.subheader("💾 Sesión")
if st.sidebar.button("Descargar Historial de Chat"):
    history_text = "# Historial de Consultas\n\n"
    for msg in st.session_state.chat_history:
        history_text += f"### {msg['role']}\n{msg['content']}\n\n---\n\n"
    
    st.sidebar.download_button(
        label="📥 Guardar como Markdown",
        data=history_text,
        file_name=f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown"
    )

if st.sidebar.button("🧹 Limpiar Historial"):
    st.session_state.chat_history = []
    st.rerun()

# 4. Debug Mode
debug_mode = st.sidebar.toggle("🛠️ Modo Debug (Ver Contexto IA)")

# --- INTERFAZ PRINCIPAL ---
st.title("⚖️ Sistema de Consulta Unificado")

# Mostrar Historial
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de Usuario
if query_text := st.chat_input("Escribe tu consulta legal aquí..."):
    # Agregar usuario al historial
    st.session_state.chat_history.append({"role": "user", "content": query_text})
    with st.chat_message("user"):
        st.markdown(query_text)

    # Procesar Consulta
    with st.chat_message("assistant"):
        with st.spinner("Analizando base normativa..."):
            # 1. Búsqueda Vectorial (Top K aumentado a 20 para mayor contexto)
            results = query_router.search(query_text, top_k=20, sources=sources_to_search)
            
            if debug_mode:
                with st.expander("🛠️ Debug: Contexto recuperado (Top 5)"):
                    for r in results[:5]:
                        st.markdown(f"**Score:** {r['score']:.4f} | **Fuente:** {r['source']}")
                        st.text(r['chunk_text'][:200] + "...")

            if results:
                # 2. Generación con IA
                respuesta = consultar_deepseek(query_text, results, system_prompt=_prompt_editado)
                st.markdown(respuesta)
                
                # Guardar respuesta en historial
                st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
                
                # Mostrar fuentes usadas en un expander
                with st.expander("📚 Ver Fuentes Consultadas"):
                    for i, res in enumerate(results[:5]): # Mostrar top 5 fuentes al usuario
                        st.markdown(f"**[{i+1}] {res['source']}** (Relevancia: {res['score']:.2f})")
                        st.caption(res['chunk_text'][:300] + "...")
            else:
                msg_error = "No se encontraron documentos relevantes en las fuentes seleccionadas."
                st.warning(msg_error)
                st.session_state.chat_history.append({"role": "assistant", "content": msg_error})