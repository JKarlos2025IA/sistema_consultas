import os
import json
import faiss
import pickle
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from pathlib import Path

class QueryRouter:
    def __init__(self, config_path='../03_CONFIG/config.json', user_config_path='../03_CONFIG/fuentes_usuario.json'):
        """
        Inicializa el enrutador de consultas.
        Carga la configuración, el modelo de embeddings y los índices.
        """
        print("Inicializando QueryRouter Híbrido...")

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_abs_path = os.path.join(self.script_dir, config_path)
        self.user_config_abs_path = os.path.join(self.script_dir, user_config_path)

        # Cargar configuración base
        with open(self.config_abs_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Cargar configuración de usuario (si existe)
        self.user_sources = []
        if os.path.exists(self.user_config_abs_path):
            try:
                with open(self.user_config_abs_path, 'r', encoding='utf-8') as f:
                    self.user_sources = json.load(f)
            except Exception as e:
                print(f"Error cargando fuentes de usuario: {e}")
        
        print("Cargando modelo de sentencias (puede tardar un momento)...")
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        self.indices = {}
        self.chunks = {}
        self.metadata = {}
        self.load_status = {}
        self.load_indices()

    def scan_directory_for_indices(self, root_path, alias=None):
        """Busca recursivamente archivos .index y sus pares json/pkl"""
        found_indices = []
        root = Path(root_path)

        if not root.exists():
            print(f"    ⚠️ Ruta no existe: {root_path}")
            return []

        # Buscar archivos .index y .bin (FAISS)
        candidate_files = list(root.rglob("*.index")) + list(root.rglob("*.bin"))

        processed_dirs = set()
        idx_count = 0

        for index_file in candidate_files:
            # Evitar duplicados si hay .index y .bin en la misma carpeta
            base_dir = index_file.parent
            if str(base_dir) in processed_dirs:
                continue

            # Asumir estructura estándar: chunks.json y metadata.pkl en la misma carpeta
            chunks_file = base_dir / "chunks.json"
            metadata_file = base_dir / "metadata.pkl"

            # Se requiere Metadata O Chunks
            if chunks_file.exists() or metadata_file.exists():
                # Usar alias del usuario si se proporciona
                if alias:
                    name = alias if idx_count == 0 else f"{alias} ({idx_count + 1})"
                else:
                    name = f"{base_dir.parent.name} - {base_dir.name}" if base_dir.name.lower() in ["embeddings", "base_vectorial"] else base_dir.name

                found_indices.append({
                    "nombre": name,
                    "ruta_indice": str(index_file),
                    "ruta_chunks": str(chunks_file) if chunks_file.exists() else None,
                    "ruta_metadata": str(metadata_file) if metadata_file.exists() else None,
                    "origen": "usuario"
                })
                processed_dirs.add(str(base_dir))
                idx_count += 1

        return found_indices

    def load_indices(self):
        """
        Carga todos los índices, chunks y metadatos (config base + usuario).
        """
        print("--- INICIANDO CARGA DE ÍNDICES ---")
        
        # 1. Índices Base (Config.json)
        indices_a_cargar = self.config['indices']

        # 2. Índices Usuario (Carpetas dinámicas)
        for source in self.user_sources:
            if source.get('activo', True):
                ruta = source['ruta']
                # Resolver rutas relativas desde el directorio del script
                if not os.path.isabs(ruta):
                    ruta = os.path.abspath(os.path.join(self.script_dir, ruta))
                alias = source.get('alias', None)
                print(f"  Escaneando ruta de usuario: {ruta} (alias: {alias})")
                encontrados = self.scan_directory_for_indices(ruta, alias=alias)
                indices_a_cargar.extend(encontrados)

        for index_info in indices_a_cargar:
            nombre = index_info['nombre']
            print(f"  Cargando índice: '{nombre}'")
            try:
                # Resolver ruta (si es absoluta usarla, si es relativa unirla)
                if os.path.isabs(index_info['ruta_indice']):
                    ruta_indice_abs = index_info['ruta_indice']
                    ruta_metadata_abs = index_info['ruta_metadata'] if index_info.get('ruta_metadata') else None
                    ruta_chunks_abs = index_info['ruta_chunks'] if index_info.get('ruta_chunks') else None
                else:
                    ruta_indice_abs = os.path.abspath(os.path.join(self.script_dir, index_info['ruta_indice']))
                    ruta_metadata_abs = os.path.abspath(os.path.join(self.script_dir, index_info['ruta_metadata']))
                    ruta_chunks_abs = os.path.abspath(os.path.join(self.script_dir, index_info['ruta_chunks']))

                # 1. Cargar Metadata (CRÍTICO)
                if ruta_metadata_abs and os.path.exists(ruta_metadata_abs):
                    with open(ruta_metadata_abs, 'rb') as f:
                        self.metadata[nombre] = pickle.load(f)
                else:
                    self.metadata[nombre] = []
                    print(f"    ⚠️ Metadata no encontrada para {nombre}")

                # 2. Cargar Índice
                self.indices[nombre] = faiss.read_index(ruta_indice_abs)
                n_vectores = self.indices[nombre].ntotal

                # 3. Cargar Textos (Chunks)
                # Intento 1: chunks.json
                loaded_chunks = False
                if ruta_chunks_abs and os.path.exists(ruta_chunks_abs):
                    try:
                        with open(ruta_chunks_abs, 'r', encoding='utf-8') as f:
                            self.chunks[nombre] = json.load(f)
                        loaded_chunks = True
                        print(f"    ✅ Chunks cargados desde chunks.json ({len(self.chunks[nombre])} textos)")
                    except Exception as e:
                        print(f"    ⚠️ Error leyendo chunks.json: {e}")

                # Intento 2: Reconstruir desde Metadata (Compatibilidad formato Docling)
                if not loaded_chunks and self.metadata[nombre]:
                    print(f"    ℹ️ Sin chunks.json. Reconstruyendo desde metadata ({len(self.metadata[nombre])} items)...")
                    reconstructed_chunks = []
                    for item in self.metadata[nombre]:
                        text = item.get('texto') or item.get('chunk_text') or item.get('content') or ""
                        reconstructed_chunks.append(text)
                    self.chunks[nombre] = reconstructed_chunks
                    loaded_chunks = True
                    n_con_texto = sum(1 for t in reconstructed_chunks if t)
                    print(f"    ✅ Reconstruidos {n_con_texto}/{len(reconstructed_chunks)} chunks con texto")

                if loaded_chunks:
                    n_chunks = len(self.chunks[nombre])
                    print(f"    -> OK: '{nombre}' | {n_vectores} vectores | {n_chunks} chunks")
                    self.load_status[nombre] = {
                        'estado': 'ok',
                        'vectores': n_vectores,
                        'chunks': n_chunks,
                        'origen': index_info.get('origen', 'config'),
                        'error_msg': None
                    }
                else:
                    msg = f"No se pudieron cargar los textos para '{nombre}'"
                    print(f"    -> ERROR: {msg}")
                    self.load_status[nombre] = {
                        'estado': 'error',
                        'vectores': n_vectores,
                        'chunks': 0,
                        'origen': index_info.get('origen', 'config'),
                        'error_msg': msg
                    }

            except FileNotFoundError as e:
                print(f"    -> ERROR: Archivo no encontrado. {e}")
                self.load_status[nombre] = {
                    'estado': 'error', 'vectores': 0, 'chunks': 0,
                    'origen': index_info.get('origen', 'config'),
                    'error_msg': f"Archivo no encontrado: {e}"
                }
            except Exception as e:
                print(f"    -> ERROR CRÍTICO al cargar '{nombre}': {e}")
                self.load_status[nombre] = {
                    'estado': 'error', 'vectores': 0, 'chunks': 0,
                    'origen': index_info.get('origen', 'config'),
                    'error_msg': str(e)
                }

        total_vectores = sum(s['vectores'] for s in self.load_status.values())
        total_ok = sum(1 for s in self.load_status.values() if s['estado'] == 'ok')
        total_err = sum(1 for s in self.load_status.values() if s['estado'] == 'error')
        print(f"--- CARGA FINALIZADA: {total_ok} OK, {total_err} errores, {total_vectores} vectores totales ---")

    def search_keyword(self, query_text, sources=None):
        """
        Búsqueda de respaldo por coincidencia exacta de texto (Keyword Search).
        Útil para términos específicos como 'entidad cesionaria'.
        """
        print(f"  [Modo Híbrido] Activando búsqueda exacta para: '{query_text}'")
        results = []
        indices_to_search = sources if sources else self.chunks.keys()
        
        query_lower = query_text.lower()
        
        for nombre_indice in indices_to_search:
            if nombre_indice not in self.chunks: continue
            
            # Recorrer todos los chunks en memoria (O(N) pero rápido para <100k chunks)
            chunks_list = self.chunks[nombre_indice]
            meta_list = self.metadata[nombre_indice]
            
            # Manejar si los chunks son lista o dict
            if isinstance(chunks_list, dict):
                items = chunks_list.items()
            else:
                items = enumerate(chunks_list)
                
            for idx, text in items:
                # Verificar coincidencia
                if query_lower in text.lower():
                    # Recuperar metadata con seguridad
                    if isinstance(meta_list, dict):
                        meta = meta_list.get(str(idx), {})
                    else:
                        meta = meta_list[idx] if idx < len(meta_list) else {}
                        
                    results.append({
                        'source': nombre_indice,
                        'score': 99.9, # Score artificialmente alto para forzar relevancia
                        'chunk_text': text,
                        'metadata': meta,
                        'method': 'keyword'
                    })
        
        return results

    def search(self, query_text, top_k=5, sources=None):
        """
        Realiza una búsqueda híbrida (Vectorial + Keyword).
        """
        if not query_text: return []

        print(f"\nRealizando búsqueda vectorizada para: '{query_text}'")
        query_vector = self.model.encode([query_text], normalize_embeddings=True).astype('float32')
        
        vector_results = []
        indices_to_search = sources if sources else self.indices.keys()

        # 1. Búsqueda Vectorial (Semántica)
        for nombre_indice in indices_to_search:
            if nombre_indice in self.indices:
                index = self.indices[nombre_indice]
                distances, indices = index.search(query_vector, top_k)
                
                for i, idx in enumerate(indices[0]):
                    if idx != -1:
                        # Metadata safe retrieval
                        meta_source = self.metadata[nombre_indice]
                        if isinstance(meta_source, dict):
                            meta = meta_source.get(str(idx), {})
                        else:
                            meta = meta_source[idx] if idx < len(meta_source) else {}

                        # Chunk safe retrieval
                        chunk_source = self.chunks[nombre_indice]
                        if isinstance(chunk_source, dict):
                            chunk = chunk_source.get(str(idx), "")
                        else:
                            chunk = chunk_source[idx] if idx < len(chunk_source) else ""

                        if chunk:
                            vector_results.append({
                                'source': nombre_indice,
                                'score': float(distances[0][i]),
                                'chunk_text': chunk,
                                'metadata': meta,
                                'method': 'vector'
                            })
        
        # 2. Lógica Híbrida: Si los resultados vectoriales son pobres o la query es específica
        # (Umbral simple: si el mejor score es bajo < 5.0 en distancia L2 inversa, o siempre para asegurar)
        # Nota: FAISS L2 devuelve distancias, menor es mejor. Aquí asumimos que los scores se ordenan.
        
        keyword_results = self.search_keyword(query_text, sources)
        
        # Combinar y desduplicar
        # Damos prioridad a Keyword si es muy específico
        combined = vector_results + keyword_results
        
        # Ordenar: Para Keyword pusimos score 99.9, para Vector usamos distancia (que deberíamos invertir o normalizar)
        # En este script simple, asumiremos que Keyword va primero si se encontró.
        
        # Truco: Invertir score de FAISS para ordenar descendente junto con Keyword
        # (FAISS L2 distance: 0 es perfecto. Keyword: 99.9 es perfecto).
        # Ajuste rápido: Si method=vector, score = 1 / (1 + distance) * 10 
        
        final_results = []
        seen_chunks = set()
        
        for res in combined:
            # Normalizar score visualmente
            if res['method'] == 'vector':
                # Faiss devuelve distancia al cuadrado. Más cerca de 0 es mejor.
                # Lo convertimos a similitud aprox para ordenar
                res['normalized_score'] = 100 / (1 + res['score'])
            else:
                res['normalized_score'] = 100.0
            
            # Desduplicar por contenido exacto
            h = hash(res['chunk_text'])
            if h not in seen_chunks:
                seen_chunks.add(h)
                final_results.append(res)
        
        sorted_results = sorted(final_results, key=lambda x: x['normalized_score'], reverse=True)
        return sorted_results[:top_k*2] # Devolver un poco más para tener variedad

if __name__ == '__main__':
    router = QueryRouter()
    
    test_query = "entidad cesionaria"
    results = router.search(test_query, top_k=3)
    
    print("\n--- Resultados Híbridos ---")
    for i, res in enumerate(results):
        print(f"\n{i+1}. [{res['method'].upper()}] Score: {res['normalized_score']:.2f} - {res['source']}")
        print(f"   Ref: {res['metadata'].get('numero_articulo', 'N/A')} - {res['metadata'].get('titulo', 'Sin título')}")
        print(f"   Texto: {res['chunk_text'][:150]}...")