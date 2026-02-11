import json
import numpy as np
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import pickle
import faiss

def create_embeddings_oece():
    """Genera embeddings unificados para opiniones OECE 2025"""
    
    base_path = Path("C:/Users/juan.montenegro/Desktop/01_BASE_NORMATIVA/006_Opiniones/Opiniones_2025_OECE")
    procesados_path = base_path / "RAG"
    output_path = base_path / "embeddings_unificados"
    output_path.mkdir(exist_ok=True)
    
    # Cargar modelo de embeddings
    print("🔄 Cargando modelo de embeddings...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # Estructuras para almacenar datos
    all_chunks = []
    all_embeddings = []
    metadata = []
    
    print("📖 Procesando archivos JSON...")
    
    # Procesar cada archivo procesado
    json_files = list(procesados_path.glob("*_CORREGIDO.json"))
    total_files = len(json_files)
    
    for i, json_file in enumerate(json_files):
        print(f"  [{i+1}/{total_files}] {json_file.name}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer chunks semánticos
        chunks_data = extract_semantic_chunks(data, json_file.stem)
        
        for chunk_data in chunks_data:
            all_chunks.append(chunk_data['text'])
            metadata.append({
                'archivo': json_file.stem,
                'numero_opinion': data.get('numero_opinion', ''),
                'fecha': data.get('fecha', ''),
                'solicitante': data.get('solicitante', ''),
                'tipo_chunk': chunk_data['tipo'],
                'normativa': data.get('normativa_principal', [])
            })
    
    print(f"📊 Total chunks: {len(all_chunks)}")
    
    # Generar embeddings
    print("🧠 Generando embeddings...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    
    # Crear índice FAISS
    print("🔗 Creando índice FAISS...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner Product para similitud coseno
    
    # Normalizar embeddings para similitud coseno
    embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    index.add(embeddings_normalized.astype('float32'))
    
    # Guardar todo
    print("💾 Guardando archivos...")
    
    # Guardar índice FAISS
    faiss.write_index(index, str(output_path / "opiniones_2025_oece.index"))
    
    # Guardar embeddings
    np.save(output_path / "embeddings.npy", embeddings_normalized)
    
    # Guardar chunks y metadata
    with open(output_path / "chunks.json", 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    with open(output_path / "metadata.pkl", 'wb') as f:
        pickle.dump(metadata, f)
    
    print(f"✅ Embeddings creados exitosamente!")
    print(f"📁 Archivos guardados en: {output_path}")
    print(f"📊 Estadísticas:")
    print(f"   - Archivos procesados: {total_files}")
    print(f"   - Chunks totales: {len(all_chunks)}")
    print(f"   - Dimensión embeddings: {dimension}")

def extract_semantic_chunks(data, filename):
    """Extrae chunks semánticos de cada opinión"""
    chunks = []
    
    # Chunk 1: Información básica
    info_basica = f"""
    Opinión: {data.get('numero_opinion', '')}
    Fecha: {data.get('fecha', '')}
    Solicitante: {data.get('solicitante', '')}
    Asunto: {data.get('asunto', '')}
    """.strip()
    
    chunks.append({
        'text': info_basica,
        'tipo': 'info_basica'
    })
    
    # Chunk 2: Consultas
    if data.get('consultas'):
        consultas_text = "CONSULTAS:\n" + "\n".join([f"- {c}" for c in data['consultas']])
        chunks.append({
            'text': consultas_text,
            'tipo': 'consultas'
        })
    
    # Chunk 3: Análisis resumido
    if data.get('analisis_resumido'):
        chunks.append({
            'text': f"ANÁLISIS: {data['analisis_resumido']}",
            'tipo': 'analisis'
        })
    
    # Chunks 4+: Conclusiones (una por chunk)
    if data.get('conclusiones'):
        for i, conclusion in enumerate(data['conclusiones']):
            chunks.append({
                'text': f"CONCLUSIÓN {i+1}: {conclusion}",
                'tipo': 'conclusion'
            })
    
    # Chunk final: Normativa
    if data.get('normativa_principal'):
        normativa_text = "NORMATIVA APLICABLE:\n" + "\n".join([f"- {n}" for n in data['normativa_principal']])
        chunks.append({
            'text': normativa_text,
            'tipo': 'normativa'
        })
    
    return chunks

if __name__ == "__main__":
    create_embeddings_oece()
