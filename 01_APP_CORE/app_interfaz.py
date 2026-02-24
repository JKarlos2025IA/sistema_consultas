import streamlit as st
from motor_busqueda import QueryRouter
import json
import hashlib
from datetime import datetime
import os
from collections import defaultdict
import requests
import pandas as pd
import re

# --- Configuración DeepSeek ---
DEEPSEEK_API_KEY = "sk-4e6b4c12e3e24d5c8296b6084aac4aac"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# --- Cache de Consultas ---
CACHE_PATH = os.path.join(os.path.dirname(__file__), '../04_LOGS/query_cache.json')
CACHE_MAX_DAYS = 7

def _get_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except:
        pass

def _cache_key(query, sources):
    raw = query.lower().strip() + "|" + "|".join(sorted(sources))
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def _cache_get(query, sources):
    cache = _get_cache()
    key = _cache_key(query, sources)
    if key in cache:
        entry = cache[key]
        try:
            fecha = datetime.fromisoformat(entry['fecha'])
            if (datetime.now() - fecha).days <= CACHE_MAX_DAYS:
                return entry['respuesta']
        except:
            pass
    return None

def _cache_set(query, sources, respuesta):
    cache = _get_cache()
    key = _cache_key(query, sources)
    cache[key] = {"query": query, "respuesta": respuesta, "fecha": datetime.now().isoformat()}
    # Limitar a 200 entradas (eliminar la más antigua si se excede)
    if len(cache) > 200:
        oldest = next(iter(cache))
        del cache[oldest]
    _save_cache(cache)

DEFAULT_PROMPT = """Eres un asesor legal experto con dominio en todas las ramas del derecho peruano: contrataciones públicas (Ley 32069, Reglamento, Directivas y Opiniones OECE), derecho civil, derecho penal, derecho administrativo y procesal.

REGLAS:
1. Responde ÚNICAMENTE con información del contexto proporcionado.
2. Cita siempre el artículo, numeral y fuente exacta.
3. Si el contexto no contiene la respuesta, dilo claramente e indica qué norma adicional se necesitaría consultar.
4. Si el contexto permite inferir una conclusión con base legal, hazlo con cautela señalando que es una inferencia.
5. Nunca inventes artículos ni atribuyas contenido que no esté en el contexto.

ESTRUCTURA DE RESPUESTA:
- **Respuesta Directa:** (Sí / No / Depende + explicación breve)
- **Fundamento Legal:** (análisis citando artículos y fuentes exactas)
- **Referencias:** (lista numerada de documentos utilizados)"""

PROMPT_TEMPLATE = """{system_prompt}

CONTEXTO DE DOCUMENTOS:
{contexto}

---
CONSULTA DEL USUARIO:
{consulta}
"""

AGENTIC_SYSTEM_PROMPT = """Eres un asesor legal experto en derecho peruano (contrataciones públicas, civil, penal, administrativo).

Tienes acceso a la herramienta search_rag para buscar en la base normativa actualizada (Ley 32069, Reglamento, Opiniones OECE, Directivas, Ley 27444, etc.).

PROCESO OBLIGATORIO:
1. Analiza la consulta del usuario
2. Planifica qué información necesitas (artículos, plazos, requisitos, etc.)
3. Usa search_rag para buscar (puedes llamarla múltiples veces con términos distintos)
4. Evalúa si lo encontrado es suficiente. Si no, busca con otros términos
5. Solo cuando tengas toda la información necesaria, responde

REGLAS DE RESPUESTA:
- Cita siempre el artículo, numeral y fuente exacta
- Nunca inventes artículos ni contenido que no esté en los resultados
- Si buscaste y no encontraste, dilo claramente
- Estructura: Respuesta Directa → Fundamento Legal → Referencias

REGLAS DE BÚSQUEDA:
- Máximo 4 búsquedas por consulta
- Si buscas un artículo específico, incluye "artículo N" en la query
- Si necesitas jurisprudencia, incluye "opinión" o "criterio OECE" en la query
- Usa términos técnicos legales, no coloquiales"""

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


def expandir_consulta(consulta_reformulada):
    """
    Genera 2 variaciones alternativas con vocabulario técnico legal diferente.
    Usa deepseek-chat (rápido/barato). Si falla, devuelve lista vacía (no rompe nada).
    """
    prompt = f"""Eres un experto en recuperación de documentos legales peruanos.
La consulta del usuario puede requerir información dispersa en varios artículos o normas.
Genera 2 sub-consultas que cubran ASPECTOS DISTINTOS de la pregunta original (no sinónimos, sino ángulos diferentes que complementen la búsqueda).
Por ejemplo: si preguntan por un proceso completo, una variación busca el inicio del proceso y otra busca los requisitos previos o documentos necesarios.
Responde SOLO con las 2 sub-consultas, una por línea, sin numeración ni explicaciones.

CONSULTA: {consulta_reformulada}"""

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 150
    }
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()
        lines = [l.strip() for l in raw.split('\n') if l.strip() and len(l.strip()) > 10]
        return lines[:2]
    except Exception:
        return []  # Fallo silencioso: el sistema sigue sin expansión


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

def actualizar_resumen_sesion(resumen_anterior, consulta_usuario, respuesta_asistente):
    """
    Actualiza el resumen acumulativo de la sesión con el nuevo turno.
    Usa deepseek-chat (rápido/barato). Si falla, devuelve el resumen anterior intacto.
    """
    prompt = f"""Eres un sintetizador de conversaciones legales peruanas.
Actualiza el resumen de la sesión incorporando el nuevo turno.
Captura: contexto del caso/procedimiento, normas o artículos discutidos, conclusiones clave.
Máximo 6 líneas. Sé muy conciso. No repitas lo que ya está en el resumen anterior.

RESUMEN ANTERIOR: {resumen_anterior if resumen_anterior else "(sesión nueva)"}

NUEVO TURNO:
Usuario: {consulta_usuario[:400]}
Asistente: {respuesta_asistente[:400]}

RESUMEN ACTUALIZADO:"""

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 300
    }
    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        nuevo = resp.json()["choices"][0]["message"]["content"].strip()
        return nuevo if nuevo else resumen_anterior
    except Exception:
        return resumen_anterior  # Fallo silencioso: el sistema sigue sin resumen actualizado


def stream_consultar_deepseek(consulta, contexto_chunks, system_prompt=None, historial=None, session_summary=""):
    """
    Versión streaming de consultar_deepseek.
    Generador que emite tokens de R1 uno a uno para st.write_stream().
    """
    if system_prompt is None:
        system_prompt = DEFAULT_PROMPT

    contexto = "\n\n".join([
        f"[{i+1}] Fuente: {c['source']} | Título: {c['metadata'].get('titulo', 'N/A')}\n{c['chunk_text']}"
        for i, c in enumerate(contexto_chunks)
    ])

    # Inyectar resumen de sesión en el system prompt si existe
    system_con_contexto = system_prompt
    if session_summary:
        system_con_contexto += f"\n\nCONTEXTO DE LA SESIÓN ACTUAL (turnos previos resumidos):\n{session_summary}"

    prompt_completo = PROMPT_TEMPLATE.format(system_prompt=system_con_contexto, contexto=contexto, consulta=consulta)

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

    messages = [{"role": "user", "content": prompt_completo}]

    payload = {
        "model": "deepseek-reasoner",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4000,
        "stream": True
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, stream=True, timeout=90)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        pass
    except Exception as e:
        yield f"\n\nError al consultar DeepSeek: {str(e)}"


def agentic_consultar_deepseek(consulta, router, sources_to_search, historial=None, max_iter=6, session_summary=""):
    """
    Fase 1 del Agentic RAG híbrido:
    - deepseek-chat con tools decide qué buscar (loop inteligente)
    - Acumula chunks únicos de todas las búsquedas
    Retorna (top_chunks, trace_busquedas)
    La Fase 2 (R1 streaming) la maneja el handler con stream_consultar_deepseek().
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_rag",
                "description": "Busca información en la base normativa legal (Ley 32069, Reglamento, Opiniones OECE, Directivas, Ley 27444). Úsala para encontrar artículos, plazos, requisitos, procedimientos, opiniones.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Texto a buscar. Usa términos técnicos legales. Ejemplo: 'artículo 60 cláusulas obligatorias contrato' o 'plazo apelación oferta'"
                        },
                        "fuentes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filtrar búsqueda a fuentes específicas. Opciones disponibles dependen de las fuentes activas. Ejemplo: ['Ley y Reglamento 32069']. Si es null, busca en todas."
                        },
                        "top_k": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 8,
                            "description": "Número de resultados a retornar. Default 4. Usa más si la pregunta es amplia."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    # Acumulador de chunks únicos para pasar a R1 al final
    gathered_chunks = []
    seen_chunk_hashes = set()

    def execute_search_rag(query, fuentes=None, top_k=4):
        sources = fuentes if fuentes else sources_to_search
        if fuentes:
            sources = [f for f in fuentes if f in router.indices]
            if not sources:
                sources = sources_to_search
        raw = router.search(query, top_k=top_k * 3, sources=sources)
        ranked = router.rerank(query, raw, top_n=top_k)
        if not ranked:
            return "No se encontraron resultados para esa búsqueda."
        lines = []
        for i, r in enumerate(ranked):
            # Acumular chunks únicos para R1
            h = hash(r['chunk_text'])
            if h not in seen_chunk_hashes:
                gathered_chunks.append(r)
                seen_chunk_hashes.add(h)
            titulo = r['metadata'].get('titulo') or r['metadata'].get('numero_opinion') or 'N/A'
            lines.append(f"[{i+1}] Fuente: {r['source']} | {titulo} | Score: {r['rerank_score']:.3f}\n{r['chunk_text']}")
        return "\n\n".join(lines)

    def get_top_chunks():
        """Ordena y limita los chunks acumulados para pasarlos a R1."""
        return sorted(gathered_chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)[:12]

    # Construir system prompt con resumen de sesión si existe
    system_content = AGENTIC_SYSTEM_PROMPT
    if session_summary:
        system_content += f"\n\nCONTEXTO DE LA SESIÓN ACTUAL (turnos previos resumidos):\n{session_summary}"

    messages = [{"role": "system", "content": system_content}]
    messages.append({"role": "user", "content": consulta})

    trace = []

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

    for iteration in range(max_iter):
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.1,
            "max_tokens": 1000  # Solo necesita decidir qué buscar, no redactar
        }
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            choice = resp.json()["choices"][0]
            msg = choice["message"]
            finish_reason = choice.get("finish_reason", "")
        except Exception as e:
            return [], trace  # chunks vacíos → el handler mostrará mensaje de error

        tool_calls = msg.get("tool_calls") or []

        if not tool_calls or finish_reason == "stop":
            # Chat terminó de buscar → devolver chunks para que el handler los pase a R1
            return get_top_chunks(), trace

        messages.append({"role": "assistant", "content": msg.get("content"), "tool_calls": tool_calls})

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])

            if fn_name == "search_rag":
                q = fn_args.get("query", "")
                fuentes = fn_args.get("fuentes")
                top_k = fn_args.get("top_k", 4)

                trace.append({
                    "iteracion": iteration + 1,
                    "query": q,
                    "fuentes": fuentes,
                    "top_k": top_k
                })

                resultado = execute_search_rag(q, fuentes, top_k)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": resultado
                })

    # Iteraciones agotadas → devolver lo que se reunió para que R1 lo sintetice
    return get_top_chunks(), trace


def verificar_citas(respuesta, chunks):
    """
    Extrae artículos citados en la respuesta de R1 y verifica cuáles tienen
    respaldo real en los chunks recuperados.
    Retorna (verificadas, no_verificadas) como sets de strings "Art. N".

    Detecta: Art. 304, Artículo 304, artículo 73.2, Arts. 60 y 61, etc.
    Verifica: que el chunk contenga esa referencia en contexto legal (no solo el número).
    """
    patron_extraccion = r'[Aa]rt(?:ículo|iculo)?s?\.?\s+(\d+(?:\.\d+)*)'
    numeros = set(re.findall(patron_extraccion, respuesta))

    if not numeros:
        return set(), set()

    verificadas = set()
    no_verificadas = set()

    for num in numeros:
        num_base = num.split('.')[0]  # "304.1" → "304"
        encontrado = False
        for chunk in chunks:
            texto = chunk['chunk_text']
            # Buscar el número en contexto de referencia legal dentro del chunk
            if re.search(rf'[Aa]rt(?:ículo|iculo)?\.?\s*{re.escape(num_base)}', texto):
                encontrado = True
                break
            # Fallback: buscar el numeral completo si tiene decimal (ej: "73.2")
            if '.' in num and re.search(rf'\b{re.escape(num)}\b', texto):
                encontrado = True
                break

        label = f"Art. {num}"
        if encontrado:
            verificadas.add(label)
        else:
            no_verificadas.add(label)

    return verificadas, no_verificadas


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
if 'prompt_personalizado' not in st.session_state:
    st.session_state.prompt_personalizado = DEFAULT_PROMPT
if 'session_summary' not in st.session_state:
    st.session_state.session_summary = ""

# --- Cargar Componentes Principales ---
query_router = load_query_router()
available_indices = sorted(list(query_router.indices.keys())) if query_router else []

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("⚖️ Consulta Legal")

_load_status = getattr(query_router, 'load_status', {})
BIBLIOTECA_ABS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../02_BIBLIOTECA_NORMATIVA'))

# === 1. FUENTE DE BÚSQUEDA (interacción principal) ===
st.sidebar.subheader("🔍 Consultar en:")

# Leer TODAS las fuentes configuradas (en memoria o no)
CONFIG_PATH_SIDEBAR = os.path.join(os.path.dirname(__file__), '../03_CONFIG/config.json')
_todas_fuentes = []

# Fuentes base (config.json)
if os.path.exists(CONFIG_PATH_SIDEBAR):
    try:
        with open(CONFIG_PATH_SIDEBAR, 'r', encoding='utf-8') as f:
            for _idx in json.load(f).get('indices', []):
                _n = _idx['nombre']
                _todas_fuentes.append({
                    "alias": _n, "activo": True, "tipo": "base",
                    "en_memoria": _n in query_router.indices,
                    "vectores": _load_status.get(_n, {}).get('vectores', 0)
                })
    except:
        pass

# Fuentes usuario (fuentes_usuario.json)
if 'alias' in st.session_state.user_sources_df.columns:
    for _, _row in st.session_state.user_sources_df.iterrows():
        _alias = _row.get('alias', '')
        _todas_fuentes.append({
            "alias": _alias,
            "activo": bool(_row.get('activo', True)),
            "tipo": "usuario",
            "en_memoria": _alias in query_router.indices,
            "vectores": _load_status.get(_alias, {}).get('vectores', 0)
        })

# Mostrar checkbox por cada fuente
_cambios_activo = False
for _f in _todas_fuentes:
    if _f['en_memoria']:
        _label = f"{_f['alias']}  ✅ ({_f['vectores']:,} vec.)"
    else:
        _label = f"{_f['alias']}  ⚪ (no cargada)"
    _nuevo_activo = st.sidebar.checkbox(_label, value=_f['activo'], key=f"chk_src_{_f['alias']}")
    if _f['tipo'] == 'usuario' and _nuevo_activo != _f['activo']:
        _mask = st.session_state.user_sources_df['alias'] == _f['alias']
        st.session_state.user_sources_df.loc[_mask, 'activo'] = _nuevo_activo
        _cambios_activo = True

if _cambios_activo:
    save_user_sources(st.session_state.user_sources_df)

if st.sidebar.button("🔄 Recargar Motor", key="btn_reload_principal"):
    st.session_state.user_sources_df = load_user_sources()
    st.cache_resource.clear()
    st.rerun()

# sources_to_search = solo lo que está actualmente en memoria
sources_to_search = list(query_router.indices.keys()) if query_router.indices else available_indices
_vec_sel = sum(_load_status.get(s, {}).get('vectores', 0) for s in sources_to_search)
st.sidebar.caption(f"En memoria: {len(sources_to_search)} fuente(s) — {_vec_sel:,} vectores")

st.sidebar.markdown("---")

# === 2. GESTIÓN DE FUENTES (mantenimiento, colapsado) ===
with st.sidebar.expander("⚙️ Gestión de Fuentes", expanded=False):

    # Agregar nueva fuente
    st.markdown("**➕ Agregar fuente:**")
    with st.form("form_add_source", clear_on_submit=True):
        new_alias = st.text_input("Alias", placeholder="Ej: Ley 27444")
        new_path = st.text_input("Ruta embeddings", placeholder="Ruta a carpeta con embeddings")
        submitted = st.form_submit_button("Guardar")
        if submitted and new_alias and new_path:
            if 'alias' in st.session_state.user_sources_df.columns and new_alias in st.session_state.user_sources_df['alias'].values:
                st.error(f"'{new_alias}' ya existe.")
            else:
                abs_path = os.path.abspath(new_path) if os.path.isabs(new_path) else os.path.abspath(os.path.join(BIBLIOTECA_ABS, new_path))
                if not os.path.exists(abs_path):
                    st.error(f"Ruta no existe: {abs_path}")
                else:
                    try:
                        rel_path = os.path.relpath(abs_path, os.path.dirname(__file__))
                        save_path = rel_path.replace("\\", "/")
                    except ValueError:
                        save_path = abs_path
                    new_row = {"activo": True, "alias": new_alias, "ruta": save_path}
                    st.session_state.user_sources_df = pd.concat(
                        [st.session_state.user_sources_df, pd.DataFrame([new_row])],
                        ignore_index=True
                    )
                    save_user_sources(st.session_state.user_sources_df)
                    st.success("Guardada. Recarga el motor.")
                    st.cache_resource.clear()
                    st.rerun()

    # Eliminar fuente de usuario
    if 'alias' in st.session_state.user_sources_df.columns:
        _user_aliases = st.session_state.user_sources_df['alias'].tolist()
        if _user_aliases:
            st.markdown("---")
            st.markdown("**🗑️ Eliminar fuente:**")
            _alias_del = st.selectbox("Fuente:", [""] + _user_aliases, key="sel_delete_fuente")
            if _alias_del:
                _del_pass = st.text_input("Clave (admin2026):", type="password", key="pass_delete_fuente")
                if st.button("Confirmar eliminación", key="btn_del_fuente"):
                    if _del_pass == "admin2026":
                        new_df = st.session_state.user_sources_df[
                            st.session_state.user_sources_df['alias'] != _alias_del
                        ].reset_index(drop=True)
                        st.session_state.user_sources_df = new_df
                        save_user_sources(new_df)
                        st.cache_resource.clear()
                        st.success(f"'{_alias_del}' eliminada.")
                        st.rerun()
                    else:
                        st.error("Clave incorrecta.")


st.sidebar.markdown("---")

# === 3. PROMPT DEL SISTEMA (colapsado, editable si se necesita) ===
with st.sidebar.expander("🤖 Prompt del sistema", expanded=False):
    _prompt_editado = st.text_area(
        "Instrucciones para la IA:",
        value=st.session_state.prompt_personalizado,
        height=220,
        key="prompt_text_area"
    )
    if _prompt_editado != st.session_state.prompt_personalizado:
        st.session_state.prompt_personalizado = _prompt_editado
    if st.button("↩️ Restaurar prompt original", key="btn_restore_prompt"):
        st.session_state.prompt_personalizado = DEFAULT_PROMPT
        st.rerun()
# Usar siempre el valor actualizado de session_state
_prompt_editado = st.session_state.prompt_personalizado

st.sidebar.markdown("---")

# === 4. HERRAMIENTAS DE SESIÓN ===
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
    st.session_state.session_summary = ""
    st.rerun()

_n_cache = len(_get_cache())
if _n_cache > 0:
    if st.sidebar.button(f"🗑️ Limpiar Caché ({_n_cache} consultas guardadas)"):
        _save_cache({})
        st.rerun()

# === 5. Debug Mode ===
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
        # 0. VERIFICAR CACHE (antes de cualquier llamada externa)
        cached_respuesta = _cache_get(query_text, sources_to_search)
        if cached_respuesta:
            if debug_mode:
                st.info("⚡ Respuesta desde caché (consulta idéntica previa)")
            st.markdown(cached_respuesta)
            st.session_state.chat_history.append({"role": "assistant", "content": cached_respuesta})
        else:
            # Fase 1: Chat busca (con spinner — el usuario sabe que está trabajando)
            with st.spinner("🤖 Analizando y buscando en base normativa..."):
                top_chunks, trace = agentic_consultar_deepseek(
                    consulta=query_text,
                    router=query_router,
                    sources_to_search=sources_to_search,
                    session_summary=st.session_state.session_summary
                )

            # Fase 2: R1 responde en streaming (aparece token a token, sin spinner)
            if top_chunks:
                respuesta = st.write_stream(stream_consultar_deepseek(
                    query_text,
                    top_chunks,
                    session_summary=st.session_state.session_summary
                ))

                # Fase 3: Verificar citas contra los chunks recuperados (anti-alucinación)
                verificadas, no_verificadas = verificar_citas(respuesta, top_chunks)
                if no_verificadas:
                    st.warning(
                        f"⚠️ **Citas sin respaldo en contexto** — verificar manualmente: "
                        f"{', '.join(sorted(no_verificadas))}"
                    )
                if verificadas:
                    st.caption(
                        f"✅ Citas verificadas en contexto: {', '.join(sorted(verificadas))}"
                    )
            else:
                respuesta = "No se encontró información relevante en las fuentes seleccionadas."
                st.warning(respuesta)

            st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
            _cache_set(query_text, sources_to_search, respuesta)

            # Fase 4: Actualizar resumen de sesión en background (fallo silencioso)
            st.session_state.session_summary = actualizar_resumen_sesion(
                st.session_state.session_summary,
                query_text,
                respuesta
            )

            if debug_mode:
                if trace:
                    with st.expander(f"🔍 Búsquedas realizadas ({len(trace)})"):
                        for t in trace:
                            st.markdown(f"**Búsqueda {t['iteracion']}:** `{t['query']}`")
                            if t['fuentes']:
                                st.caption(f"Fuentes: {', '.join(t['fuentes'])} | top_k={t['top_k']}")
                            else:
                                st.caption(f"Fuentes: todas | top_k={t['top_k']}")
                if st.session_state.session_summary:
                    with st.expander("🧠 Resumen de sesión (contexto acumulado)"):
                        st.markdown(st.session_state.session_summary)