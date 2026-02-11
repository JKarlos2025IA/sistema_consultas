@echo off
echo === CREANDO EMBEDDINGS UNIFICADOS OECE 2025 ===
echo.
echo Instalando dependencias...
pip install sentence-transformers faiss-cpu
echo.
echo Generando embeddings...
python create_embeddings.py
echo.
echo ✅ Proceso completado
pause
