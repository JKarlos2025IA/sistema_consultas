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

def reformular_consulta(consulta, historial_chat=None):
    """
    Reformula la consulta usando deepseek-chat (rápido y barato).
    Corrige typos, expande sinónimos legales, resuelve referencias contextuales.
    """
    # Construir contexto de historial (últimos 3 turnos)
    contexto_historial = ""
    if historial_chat and len(historial_chat) > 0:
        ultimos_turnos = historial_chat[-6:]  # 3 turnos = 6 mensajes (user+assistant)
        turnos_texto = []
        for msg in ultimos_turnos:
            rol = "Usuario" if msg["role"] == "user" else "Asistente"
            # Truncar respuestas largas del asistente
            contenido = msg["content"][:300] if msg["role"] == "assistant" else msg["content"]
            turnos_texto.append(f"{rol}: {contenido}")
        contexto_historial = "\n".join(turnos_texto)

    prompt_reformulacion = f"""Eres un reformulador de consultas legales peruanas. Tu tarea es mejorar la consulta del usuario para búsqueda vectorial.

REGLAS:
1. Corrige errores ortográficos y de tipeo
2. Expande abreviaciones legales (LCE=Ley de Contrataciones del Estado, RLCE=Reglamento, OSCE/OECE=Organismo Supervisor)
3. Si hay historial previo, resuelve referencias como "eso", "lo anterior", "y los plazos?", "dicho artículo"
4. Mantén el sentido original - NO agregues información nueva
5. Responde SOLO con la consulta reformulada, sin explicaciones

{f"HISTORIAL RECIENTE:{chr(10)}{contexto_historial}" if contexto_historial else ""}

CONSULTA ORIGINAL: {consulta}

CONSULTA REFORMULADA:"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_reformulacion}],
        "temperature": 0.1,
        "max_tokens": 200
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        query_mejorada = response.json()["choices"][0]["message"]["content"].strip()
        # Sanidad: si la respuesta es muy larga o vacía, usar original
        if not query_mejorada or len(query_mejorada) > 500:
            return consulta
        return query_mejorada
    except Exception:
        return consulta  # Fallback seguro: query original


def consultar_deepseek(consulta, contexto_chunks, system_prompt=None, historial=None):
    """Envía consulta a DeepSeek con el contexto de los documentos encontrados y historial conversacional"""
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

    # Construir mensajes con historial conversacional (últimos 3 turnos)
    messages = []
    if historial and len(historial) > 0:
        ultimos = historial[-6:]  # 3 turnos = 6 mensajes
        for msg in ultimos:
            messages.append({"role": msg["role"], "content": msg["content"][:500]})

    # Mensaje actual con contexto RAG completo
    messages.append({"role": "user", "content": prompt_completo})

    payload = {
        "model": "deepseek-reasoner",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4000
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
    df = pd.DataFrame(columns=["activo", "alias", "ruta"])
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                loaded_df = pd.DataFrame(data)
                # Asegurar que existan todas las columnas
                for col in ["activo", "alias", "ruta"]:
                    if col not in loaded_df.columns:
                        loaded_df[col] = "" if col == "ruta" or col == "alias" else True
                return loaded_df
        except:
            pass
    return df

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
# LEER DIRECTAMENTE DEL DISCO para evitar "zombies" en caché
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../03_CONFIG/config.json')
indices_base_disk = []
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            _cfg = json.load(f)
            indices_base_disk = _cfg.get('indices', [])
    except:
        indices_base_disk = []

if indices_base_disk:
    for idx_info in indices_base_disk:
        nombre = idx_info['nombre']
        status = _load_status.get(nombre, {})
        vec = status.get('vectores', 0) if status.get('estado') == 'ok' else 0
        
        # Lógica del Check Verde: ¿Está realmente en memoria?
        en_memoria = nombre in query_router.indices
        estado_visual = "✅ Listo" if en_memoria else "⚪ Inactivo"
        
        _filas_unificadas.append({
            "Cargar": True, 
            "Estado": estado_visual,
            "Nombre": nombre, 
            "Vectores": vec, 
            "_tipo": "base"
        })

# Indices usuario (fuentes_usuario.json)
# Asegurar que user_sources_df tenga estructura correcta antes de iterar
if 'alias' not in st.session_state.user_sources_df.columns:
    st.session_state.user_sources_df = pd.DataFrame(columns=["activo", "alias", "ruta"])

for _, row in st.session_state.user_sources_df.iterrows():
    alias = row.get('alias', '')
    activo = row.get('activo', True)
    status = _load_status.get(alias, {})
    vec = status.get('vectores', 0) if status.get('estado') == 'ok' else 0
    
    # Lógica del Check Verde para usuario
    en_memoria = alias in query_router.indices
    estado_visual = "✅ Listo" if en_memoria else "⚪ Inactivo"
    
    # Guardamos la ruta oculta para no perderla
    _filas_unificadas.append({
        "Cargar": activo, 
        "Estado": estado_visual,
        "Nombre": alias, 
        "Vectores": vec, 
        "_tipo": "usuario", 
        "ruta": row.get('ruta', '')
    })

_df_unificada = pd.DataFrame(_filas_unificadas)

if not _df_unificada.empty:
    edited_sources = st.sidebar.data_editor(
        _df_unificada[["Cargar", "Estado", "Nombre", "Vectores", "_tipo"]], # Mostramos columnas relevantes
        column_config={
            "Cargar": st.column_config.CheckboxColumn("Cargar", help="Marca para incluir en la próxima recarga", default=True),
            "Estado": st.column_config.TextColumn("Status", disabled=True, width="small"),
            "Nombre": st.column_config.TextColumn("Fuente"),
            "Vectores": st.column_config.NumberColumn("Vec.", disabled=True, width="small"),
            "_tipo": st.column_config.TextColumn("Tipo", disabled=True, width="small"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="unified_sources"
    )
    
    # --- LOGICA DE ACTUALIZACION Y BORRADO ---
    # 1. Detectar cambios en fuentes de USUARIO
    user_edited = edited_sources[edited_sources["_tipo"] == "usuario"]
    
    # 2. Verificar si hubo cambios en la lista de fuentes (Borrado)
    current_aliases = st.session_state.user_sources_df['alias'].tolist()
    edited_aliases = user_edited['Nombre'].tolist()
    
    # Si faltan alias (alguien borró filas)
    if len(edited_aliases) < len(current_aliases):
        # Identificar qué se quiere borrar
        deleted_aliases = list(set(current_aliases) - set(edited_aliases))
        
        st.sidebar.warning(f"Eliminar: {', '.join(deleted_aliases)}")
        del_pass = st.sidebar.text_input("Clave para confirmar borrado:", type="password", key="del_pass_fuentes_new")
        
        col_d1, col_d2 = st.sidebar.columns(2)
        with col_d1:
            if st.button("Confirmar Borrado", key="btn_confirm_del"):
                if del_pass == "admin2026":
                    # Proceder al borrado real
                    # Reconstruimos el DF de usuario manteniendo las rutas originales de los que quedan
                    alias_to_path = dict(zip(st.session_state.user_sources_df['alias'], st.session_state.user_sources_df['ruta']))
                    
                    new_rows = []
                    for _, row in user_edited.iterrows():
                        name = row["Nombre"]
                        path = alias_to_path.get(name, "")
                        if path: 
                            new_rows.append({"activo": row["Cargar"], "alias": name, "ruta": path})
                    
                    # 1. Actualizar Dataframe en Memoria
                    df_to_save = pd.DataFrame(new_rows)
                    if df_to_save.empty: 
                         df_to_save = pd.DataFrame(columns=["activo", "alias", "ruta"])

                    # 2. Guardado "Fuerte" en Disco
                    save_user_sources(df_to_save)
                    
                    # 3. Sincronización Nuclear (Evitar Zombies)
                    st.session_state.user_sources_df = load_user_sources() # Releer del disco para estar 100% seguros
                    st.cache_resource.clear() # Eliminar caché del motor (QueryRouter)
                    
                    st.success("Fuente eliminada y caché purgada correctamente.")
                    st.rerun()
                else:
                    st.sidebar.error("Clave incorrecta.")
        with col_d2:
             # Si no confirma, simplemente no hacemos nada (el estado visual volverá al original al recargar si no se guarda)
             if st.button("Cancelar", key="btn_cancel_del"):
                 st.rerun()
        
    # 3. Verificar cambios solo en "Activo" (Checkbox) sin borrar filas
    elif len(edited_aliases) == len(current_aliases):
        # Check if 'activo' status changed
        has_changes = False
        for index, row in user_edited.iterrows():
            alias = row["Nombre"]
            new_active = row["Cargar"]
            
            mask = st.session_state.user_sources_df['alias'] == alias
            if mask.any():
                current_active = st.session_state.user_sources_df.loc[mask, 'activo'].values[0]
                if current_active != new_active:
                    st.session_state.user_sources_df.loc[mask, 'activo'] = new_active
                    has_changes = True
        
        if has_changes:
            save_user_sources(st.session_state.user_sources_df)

    sources_to_search = edited_sources[edited_sources["Cargar"] == True]["Nombre"].tolist()
else:
    sources_to_search = available_indices

# Agregar nueva fuente (st.form evita doble registro)
BIBLIOTECA_ABS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../02_BIBLIOTECA_NORMATIVA'))

with st.sidebar.expander("➕ Agregar Nueva Fuente", expanded=False):
    with st.form("form_add_source", clear_on_submit=True):
        new_alias = st.text_input("Alias", placeholder="Ej: LEY 27444")
        new_path = st.text_input("Ruta de Embeddings", placeholder="Carpeta dentro de 02_BIBLIOTECA_NORMATIVA")
        submitted = st.form_submit_button("Guardar")
        if submitted and new_alias and new_path:
            # VALIDACION: Verificar si ya existe
            if new_alias in st.session_state.user_sources_df['alias'].values:
                st.error(f"⚠️ El alias '{new_alias}' ya existe. Usa otro nombre.")
            else:
                # Convertir ruta absoluta a relativa si apunta a la biblioteca
                abs_path = os.path.abspath(new_path) if os.path.isabs(new_path) else os.path.abspath(os.path.join(BIBLIOTECA_ABS, new_path))
                if not os.path.exists(abs_path):
                    st.error(f"🚫 La ruta no existe: {abs_path}")
                else:
                    # Guardar siempre como ruta relativa desde 01_APP_CORE
                    try:
                        rel_path = os.path.relpath(abs_path, os.path.dirname(__file__))
                        save_path = rel_path.replace("\\", "/")
                    except ValueError:
                        save_path = abs_path  # Fallback si están en discos distintos
                    new_row = {"activo": True, "alias": new_alias, "ruta": save_path}
                    st.session_state.user_sources_df = pd.concat(
                        [st.session_state.user_sources_df, pd.DataFrame([new_row])],
                        ignore_index=True
                    )
                    save_user_sources(st.session_state.user_sources_df)
                    st.success("Guardado.")
                    st.cache_resource.clear()
                    st.rerun()

if st.sidebar.button("🔄 Cargar / Actualizar Motor"):
    # 1. Limpiar widget data_editor para que se reconstruya con datos frescos
    if "unified_sources" in st.session_state:
        del st.session_state["unified_sources"]
    # 2. Re-leer fuentes del disco (por si hubo cambios de checkbox no sincronizados)
    st.session_state.user_sources_df = load_user_sources()
    # 3. Limpiar cache del motor para que QueryRouter recargue con las fuentes activas
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

# Mostrar versión y fecha de última actualización (del último commit git)
import subprocess
try:
    _last_commit = subprocess.check_output(
        ["git", "log", "-1", "--format=%ai"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        stderr=subprocess.DEVNULL
    ).decode().strip()
    st.caption(f"Última actualización: {_last_commit}")
except Exception:
    st.caption(f"Sesión iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

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
        with st.spinner("Analizando consulta..."):
            # 1. REFORMULACIÓN (siempre activa, invisible)
            query_busqueda = reformular_consulta(query_text, st.session_state.chat_history)

        with st.spinner("Buscando en base normativa..."):
            # 2. BÚSQUEDA con query mejorada
            results = query_router.search(query_busqueda, top_k=20, sources=sources_to_search)

        with st.spinner("Filtrando resultados..."):
            # 3. RE-RANKING (siempre activo, invisible)
            results_final = query_router.rerank(query_busqueda, results, top_n=7)

        if debug_mode:
            if query_busqueda != query_text:
                st.info(f"**Query original:** {query_text}\n\n**Query reformulada:** {query_busqueda}")
            with st.expander("🛠️ Debug: Chunks recuperados"):
                for r in results_final:
                    st.markdown(f"**Rerank:** {r['rerank_score']:.4f} | **Fuente:** {r['source']} | **Método:** {r.get('method', 'N/A')}")
                    st.text(r['chunk_text'][:200] + "...")

        if results_final:
            # 4. RESPUESTA con R1 + historial conversacional
            respuesta = consultar_deepseek(
                query_text, results_final,
                system_prompt=_prompt_editado,
                historial=st.session_state.chat_history
            )
            st.markdown(respuesta)
            st.session_state.chat_history.append({"role": "assistant", "content": respuesta})

            with st.expander("📚 Ver Fuentes Consultadas"):
                for i, res in enumerate(results_final):
                    st.markdown(f"**[{i+1}] {res['source']}** (Similitud: {res['rerank_score']:.3f})")
                    st.caption(res['chunk_text'][:300] + "...")
        else:
            msg_error = "No se encontraron documentos relevantes en las fuentes seleccionadas."
            st.warning(msg_error)
            st.session_state.chat_history.append({"role": "assistant", "content": msg_error})