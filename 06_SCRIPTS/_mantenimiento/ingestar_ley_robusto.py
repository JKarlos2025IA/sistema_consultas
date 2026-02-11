import os
import re
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Rutas
BASE_DIR = r"G:\Mi unidad\01_BASE_NORMATIVA\005_Ley_reglamento_32069\Ley_y_reglamento_32069_pdf\actualizacion"
OUTPUT_DIR = os.path.join(BASE_DIR, "embeddings_ley_actualizada")

ARCHIVOS_ENTRADA = [
    {"archivo": "Ley_32069_ocr.md", "tipo": "Ley 32069"},
    {"archivo": "Reglamento_32069_ocr.md", "tipo": "Reglamento 32069"}
]

def limpiar_contenido(texto):
    """
    Elimina marcadores de página y unifica el texto.
    """
    lineas = texto.split('\n')
    lineas_limpias = []
    for linea in lineas:
        # Eliminar marcadores de página tipo "# Página X"
        if re.match(r'^# Página \d+', linea.strip()):
            continue
        lineas_limpias.append(linea)
    return "\n".join(lineas_limpias)

def segmentar_por_articulos(texto, nombre_archivo, tipo_norma):
    """
    Divide el texto en chunks basados en 'Artículo X.'
    """
    # Patrón: "Artículo" seguido de número, punto y un espacio o salto de línea
    # Se usa lookahead para no consumir el inicio del siguiente artículo en el split
    patron_split = r'(?=^Artículo \d+\.)'
    
    # Dividir. El flag re.MULTILINE es clave para que ^ funcione en cada línea
    segmentos = re.split(patron_split, texto, flags=re.MULTILINE)
    
    chunks_procesados = []
    
    for seg in segmentos:
        seg = seg.strip()
        if not seg:
            continue
            
        # Verificar si realmente es un artículo (el split puede dejar basura al inicio)
        match_num = re.match(r'Artículo (\d+)\.', seg)
        if match_num:
            numero_art = match_num.group(1)
            titulo_match = re.search(r'Artículo \d+\.\s*(.+?)(?:\n|$)', seg)
            titulo = titulo_match.group(1).strip() if titulo_match else "Sin título"
            
            # Crear metadatos ricos
            meta = {
                "source": tipo_norma,
                "archivo": nombre_archivo,
                "numero_articulo": numero_art,
                "titulo": titulo,
                "tipo_chunk": "articulo"
            }
            
            # Formato de texto para el embedding (Contexto + Contenido)
            texto_embedding = f"{tipo_norma} - Artículo {numero_art}: {titulo}\n{seg}"
            
            chunks_procesados.append({
                "texto_completo": seg,
                "texto_embedding": texto_embedding,
                "metadata": meta
            })
        else:
            # Es texto introductorio o anexos (Disposiciones, Títulos preliminares, etc.)
            # Lo guardamos como "Otro" si tiene longitud relevante
            if len(seg) > 100:
                chunks_procesados.append({
                    "texto_completo": seg,
                    "texto_embedding": f"{tipo_norma} - Fragmento: {seg[:100]}...",
                    "metadata": {
                        "source": tipo_norma,
                        "archivo": nombre_archivo,
                        "numero_articulo": "N/A",
                        "titulo": "Sección no articulada (Intro/Anexo)",
                        "tipo_chunk": "seccion_general"
                    }
                })
                
    return chunks_procesados

def main():
    print("--- INICIANDO INGESTA DE LEY Y REGLAMENTO 32069 ---")
    
    todos_los_chunks = []
    
    # 1. Procesar Textos
    for item in ARCHIVOS_ENTRADA:
        ruta = os.path.join(BASE_DIR, item['archivo'])
        if not os.path.exists(ruta):
            print(f"⚠️ Advertencia: No se encuentra {ruta}")
            continue
            
        print(f"📖 Leyendo: {item['archivo']}...")
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido_bruto = f.read()
            
        print(f"   Limpiando saltos de página...")
        contenido_limpio = limpiar_contenido(contenido_bruto)
        
        print(f"   Segmentando por Artículos...")
        chunks = segmentar_por_articulos(contenido_limpio, item['archivo'], item['tipo'])
        
        print(f"   -> Encontrados {len(chunks)} segmentos en {item['archivo']}")
        todos_los_chunks.extend(chunks)

    print(f"\nTOTAL SEGMENTOS A VECTORIZAR: {len(todos_los_chunks)}")
    
    # 2. Vectorizar
    print("\n🧠 Cargando modelo de embeddings (MiniLM-L12)...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    textos_para_vectorizar = [c['texto_embedding'] for c in todos_los_chunks]
    
    print("🚀 Generando vectores (esto puede tardar unos segundos)...")
    embeddings = model.encode(textos_para_vectorizar, show_progress_bar=True)
    
    # 3. Crear Índice FAISS
    print("\n📦 Creando índice FAISS...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    
    # 4. Guardar Todo
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    ruta_index = os.path.join(OUTPUT_DIR, "ley_actualizada.index")
    ruta_chunks = os.path.join(OUTPUT_DIR, "chunks.json")
    ruta_meta = os.path.join(OUTPUT_DIR, "metadata.pkl")
    
    print(f"💾 Guardando en {OUTPUT_DIR}...")
    
    faiss.write_index(index, ruta_index)
    
    # Guardamos solo el texto en JSON para lectura humana/rápida
    chunks_text_only = [c['texto_completo'] for c in todos_los_chunks]
    with open(ruta_chunks, 'w', encoding='utf-8') as f:
        json.dump(chunks_text_only, f, ensure_ascii=False, indent=2)
        
    # Guardamos metadatos completos en Pickle
    metadata_list = [c['metadata'] for c in todos_los_chunks]
    with open(ruta_meta, 'wb') as f:
        pickle.dump(metadata_list, f)
        
    print("\n✅ PROCESO COMPLETADO EXITOSAMENTE.")
    print(f"   - Artículos Ley: {len([c for c in todos_los_chunks if c['metadata']['source'] == 'Ley 32069' and c['metadata']['tipo_chunk'] == 'articulo'])}")
    print(f"   - Artículos Reglamento: {len([c for c in todos_los_chunks if c['metadata']['source'] == 'Reglamento 32069' and c['metadata']['tipo_chunk'] == 'articulo'])}")

if __name__ == "__main__":
    main()
