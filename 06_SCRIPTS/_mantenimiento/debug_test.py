import json
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# --- Configuración de la Prueba ---
CONFIG_PATH = 'config.json'
INDEX_NAME_TO_TEST = 'Opiniones 2022'
TEST_QUERY = 'contrataciones directas'

def run_debug_test():
    print(f"--- Iniciando prueba de depuración para el índice: '{INDEX_NAME_TO_TEST}' ---")

    # 1. Cargar configuración
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("OK - Archivo de configuración cargado.")
    except Exception as e:
        print(f"ERROR - No se pudo cargar el archivo de configuración: {e}")
        return

    # 2. Encontrar la información del índice a probar
    index_info = next((item for item in config['indices'] if item["nombre"] == INDEX_NAME_TO_TEST), None)
    if not index_info:
        print(f"ERROR - No se encontró el índice '{INDEX_NAME_TO_TEST}' en {CONFIG_PATH}")
        return
    print(f"OK - Configuración encontrada para '{INDEX_NAME_TO_TEST}'.")

    # 3. Cargar los artefactos (índice, chunks, metadata)
    try:
        index = faiss.read_index(index_info['ruta_indice'])
        print(f"OK - Índice FAISS cargado desde: {index_info['ruta_indice']}")
        
        with open(index_info['ruta_chunks'], 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        print(f"OK - Chunks JSON cargados desde: {index_info['ruta_chunks']}")
        
        with open(index_info['ruta_metadata'], 'rb') as f:
            metadata = pickle.load(f)
        print(f"OK - Metadata Pickle cargada desde: {index_info['ruta_metadata']}")

    except Exception as e:
        print(f"ERROR - Fallo al cargar uno de los archivos del índice: {e}")
        return

    # 4. Verificar consistencia de los datos
    print("\n--- Verificando Consistencia de Datos ---")
    num_vectors = index.ntotal
    num_chunks = len(chunks)
    num_metadata = len(metadata)

    print(f"Vectores en índice FAISS: {num_vectors}")
    print(f"Entradas en chunks.json: {num_chunks}")
    print(f"Entradas en metadata.pkl: {num_metadata}")

    if not (num_vectors == num_chunks == num_metadata):
        print("¡ALERTA! El número de entradas no coincide entre los archivos. Este es un problema crítico.")
    else:
        print("OK - El número de entradas es consistente en todos los archivos.")

    # 5. Realizar una búsqueda de prueba
    print(f"\n--- Realizando Búsqueda de Prueba ---")
    try:
        print("Cargando modelo de sentencias...")
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        print(f"Generando vector para la consulta: '{TEST_QUERY}'")
        query_vector = model.encode([TEST_QUERY], normalize_embeddings=True).astype('float32')
        
        print(f"Buscando los 5 resultados más cercanos...")
        distances, indices = index.search(query_vector, 5)
        
        print("\n--- Resultados Obtenidos ---")
        if not np.any(indices[0] != -1):
            print("La búsqueda no arrojó ningún resultado válido.")
            return

        for i, idx in enumerate(indices[0]):
            if idx != -1:
                score = distances[0][i]
                chunk_text = chunks.get(str(idx), "[CHUNK NO ENCONTRADO]")
                meta_info = metadata.get(str(idx), "[METADATA NO ENCONTRADA]")
                print(f"\nResultado {i+1} (Índice: {idx}, Score: {score:.4f})")
                print(f"  Chunk: {chunk_text[:200]}...")
                print(f"  Metadata: {meta_info}")
            else:
                print(f"\nResultado {i+1}: No válido (índice -1)")

    except Exception as e:
        print(f"ERROR - La búsqueda de prueba falló: {e}")

if __name__ == "__main__":
    run_debug_test()
