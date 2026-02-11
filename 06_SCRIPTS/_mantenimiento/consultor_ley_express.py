import os
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import argparse

# Configuración de rutas (ajustadas a donde están los archivos generados)
BASE_DIR = r"G:\Mi unidad\01_BASE_NORMATIVA\005_Ley_reglamento_32069\Ley_y_reglamento_32069_pdf\actualizacion\embeddings_ley_actualizada"
INDEX_PATH = os.path.join(BASE_DIR, "ley_actualizada.index")
CHUNKS_PATH = os.path.join(BASE_DIR, "chunks.json")
META_PATH = os.path.join(BASE_DIR, "metadata.pkl")

def cargar_sistema():
    print("⏳ Cargando sistema de consulta legal...")
    
    # 1. Cargar Índice FAISS
    if not os.path.exists(INDEX_PATH):
        print(f"❌ Error: No se encuentra el índice en {INDEX_PATH}")
        return None, None, None, None
    
    index = faiss.read_index(INDEX_PATH)
    
    # 2. Cargar Textos y Metadatos
    with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    with open(META_PATH, 'rb') as f:
        metadata = pickle.load(f)
        
    # 3. Cargar Modelo (Esto tarda un poco la primera vez)
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    print("✅ Sistema listo.")
    return index, chunks, metadata, model

def consultar(pregunta, top_k=3):
    index, chunks, metadata, model = cargar_sistema()
    if not index:
        return

    print(f"\n🔎 Buscando respuesta para: '{pregunta}'\n")
    
    # Vectorizar pregunta
    vec_pregunta = model.encode([pregunta]).astype('float32')
    
    # Buscar en FAISS
    distances, indices = index.search(vec_pregunta, top_k)
    
    print(f"Resultados encontrados ({top_k} mejores):")
    print("="*60)
    
    for i, idx in enumerate(indices[0]):
        if idx == -1: continue
        
        score = distances[0][i]
        texto = chunks[idx]
        meta = metadata[idx]
        
        print(f"🏆 RANGO #{i+1} (Similitud: {score:.4f})")
        print(f"📄 Fuente: {meta['source']}")
        print(f"📌 Artículo: {meta['numero_articulo']} - {meta['titulo']}")
        print("-" * 30)
        # Mostrar primeros 500 caracteres del texto para no saturar pantalla
        print(texto[:500] + "..." if len(texto) > 500 else texto)
        print("\n" + "="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consultor Ley 32069")
    parser.add_argument("pregunta", type=str, help="Tu pregunta legal")
    args = parser.parse_args()
    
    consultar(args.pregunta)
