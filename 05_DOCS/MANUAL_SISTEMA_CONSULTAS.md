# Sistema RAG con IA - Base Normativa de Contrataciones

## Resumen del Sistema

| Componente | Descripcion |
|------------|-------------|
| **Busqueda** | FAISS + Sentence Transformers (busqueda semantica) |
| **IA** | DeepSeek API (respuestas fundamentadas) |
| **Interfaz** | Streamlit (web local) |
| **Documentos** | Opiniones OECE/OSCE parseadas |

---

## 1. Como Funciona

### Flujo Completo
```
PDF → OCR → TXT → Parser → JSON → Embeddings → FAISS → Busqueda → IA → Respuesta
```

### Dos Modos de Consulta

| Boton | Que hace |
|-------|----------|
| **Buscar** | Solo muestra los chunks relevantes (sin IA) |
| **Consultar con IA** | Busca + envia contexto a DeepSeek + genera respuesta fundamentada |

### Arquitectura
```
[Tu pregunta]
    ↓
[Streamlit] → [FAISS busca chunks relevantes]
    ↓
[15 chunks mas relevantes]
    ↓
[DeepSeek IA recibe: System Prompt + Chunks + Pregunta]
    ↓
[Respuesta citando opiniones]
```

---

## 2. Archivos del Sistema

### Carpeta Principal: `000_CONSULTAS/`
```
000_CONSULTAS/
├── 00_START.bat           # Ejecutar para iniciar
├── config.json            # Registro de indices disponibles
├── core_interfaz.py       # Streamlit + integracion DeepSeek
├── core_motor_busqueda.py # QueryRouter (busqueda hibrida)
└── historial_consultas/   # JSONs de consultas guardadas
```

### Carpeta de Scripts: `03_PROJECTS/0003_Scprits/`
```
Parser_Legal/
├── parser_opiniones.py    # Convierte TXT a JSON estructurado
├── parser_opiniones.bat   # Ejecutable Windows
├── auditar_parser.py      # Verifica calidad de JSONs
├── auditar_parser.bat     # Ejecutable Windows
└── ESTADO_PROYECTO.md     # Documentacion del proyecto

Embedding_Legal/
├── generar_embeddings.py      # Genera vectores FAISS para opiniones (incremental)
├── generar_embeddings.bat     # Ejecutable Windows
├── generar_embeddings_ley.py  # Genera vectores FAISS para Ley/Reglamento MD
├── generar_embeddings_ley.bat # Ejecutable Windows
├── exportar_a_sistema.py      # Convierte al formato del sistema RAG
└── buscar.py                  # Buscador standalone para pruebas
```

---

## 3. Como Agregar Nuevas Opiniones

### Paso 1: Convertir PDF a TXT
Usar OCR (Tesseract o Google Vision) para convertir PDFs a TXT.

### Paso 2: Parsear TXT a JSON
```bash
python parser_opiniones.py "ruta/carpeta_txt"
```
Genera JSONs estructurados en `Procesados_Parser/`

### Paso 3: Auditar Calidad
```bash
python auditar_parser.py "ruta/Procesados_Parser"
```
Verifica que los JSONs tengan metadata y contenido correcto.

### Paso 4: Generar Embeddings
```bash
python generar_embeddings.py "ruta/Procesados_Parser" "ruta/Embeddings"
```
Genera vectores FAISS (incremental - solo procesa nuevos).

### Paso 5: Exportar al Sistema RAG
```bash
python exportar_a_sistema.py "ruta/Embeddings" "ruta/carpeta_opiniones" "nombre_indice"
```
Crea carpeta `embeddings_unificados/` con formato compatible.

### Paso 6: Registrar en config.json
```json
{
    "indices": [
        {
            "nombre": "Opiniones OECE 2025",
            "descripcion": "Opiniones del 2025",
            "ruta_indice": "../006_Opiniones/Opiniones_2025_OECE/embeddings_unificados/opiniones_2025_oece.index",
            "ruta_chunks": "../006_Opiniones/Opiniones_2025_OECE/embeddings_unificados/chunks.json",
            "ruta_metadata": "../006_Opiniones/Opiniones_2025_OECE/embeddings_unificados/metadata.pkl"
        }
    ]
}
```

### Paso 7: Reiniciar Sistema
Cerrar y ejecutar `00_START.bat` nuevamente.

---

## 4. Comandos Rapidos

### Parser
```bash
# Procesar nuevos TXT (incremental)
python parser_opiniones.py "carpeta_txt"

# Forzar reprocesamiento
python parser_opiniones.py "carpeta_txt" --force

# Auditar resultados
python auditar_parser.py "carpeta_Procesados_Parser"
```

### Embeddings (Opiniones)
```bash
# Generar embeddings (incremental)
python generar_embeddings.py "carpeta_jsons" "carpeta_salida"

# Regenerar todo
python generar_embeddings.py "carpeta_jsons" "carpeta_salida" --force

# Actualizar archivo especifico
python generar_embeddings.py "carpeta_jsons" "carpeta_salida" --update archivo.json
```

### Embeddings (Ley y Reglamento)
```bash
# Generar embeddings desde archivos MD
python generar_embeddings_ley.py "carpeta_mds" "carpeta_salida"

# Ejemplo para Ley 32069
python generar_embeddings_ley.py ".../005_Ley_reglamento_32069" ".../005_Ley_reglamento_32069/Embeddings"
```

### Busqueda (pruebas)
```bash
# Busqueda directa
python buscar.py "carpeta_embeddings" "tu consulta aqui"

# Modo interactivo
python buscar.py "carpeta_embeddings"
```

---

## 5. Configuracion de la IA

### API DeepSeek
La API key esta configurada en `core_interfaz.py`:
```python
DEEPSEEK_API_KEY = "sk-..."
```

### System Prompt
El prompt instruye a la IA para:
- Responder SOLO con informacion del contexto
- Citar siempre numero de opinion y fecha
- Buscar las CONCLUSIONES de las opiniones
- Diferenciar entre Ley 30225 (anterior) y Ley 32069 (nueva)

---

## 6. Estado Actual del Proyecto

### Indices Activos
| Indice | Documentos | Vectores | Estado |
|--------|------------|----------|--------|
| Opiniones OECE 2025 | 68 | 1,369 | Activo |
| Ley y Reglamento 32069 | 2 (Ley + Reglamento) | 1,153 | Activo |

### Indices Pendientes
- Opiniones OSCE 2025 (separar y procesar)
- Opiniones 2024, 2023, 2022 (reprocesar con nuevo parser)
- Opiniones 2026 (procesar)

### Archivos con Problemas (revision manual)
Ver `Parser_Legal/ESTADO_PROYECTO.md` para lista de 11 archivos pendientes.

---

## 7. Troubleshooting

### Error: "No such file or directory"
- Verificar que las rutas en `config.json` sean correctas
- Usar rutas relativas (`../006_Opiniones/...`)

### Error: "charmap codec can't encode"
- Los scripts usan UTF-8, la consola Windows puede fallar con emojis
- Se usan caracteres ASCII en lugar de emojis

### La IA no encuentra la respuesta correcta
- Aumentar `top_k` en la busqueda (actualmente 15)
- Verificar que el chunk con la conclusion este en el indice
- Probar con terminos mas especificos

### Embeddings no se actualizan
- Usar `--force` para regenerar todo
- Verificar que el archivo este en `procesados.log`

---

## 8. Proximos Pasos

1. [x] Generar embeddings de Ley 32069 - COMPLETADO
2. [ ] Procesar opiniones 2026
3. [ ] Reprocesar 2024/2023/2022 con nuevo parser
4. [ ] Revisar 11 archivos con problemas de OCR
5. [ ] Agregar mas fuentes (directivas, resoluciones)

---

*Ultima actualizacion: 2026-02-05*
*Version del sistema: 2.1 - Incluye Ley y Reglamento 32069*
