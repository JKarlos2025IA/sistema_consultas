import sys
import subprocess
import os

# El objetivo es ejecutar Streamlit desde dentro de Python para evitar problemas de PATH.

# 1. Definir la ruta absoluta a la carpeta de la interfaz
app_dir = os.path.dirname(os.path.abspath(__file__))
app_file = os.path.join(app_dir, 'interfaz_streamlit.py')

print(f"Directorio de la aplicacion: {app_dir}")
print(f"Archivo de la aplicacion: {app_file}")

# 2. Construir el comando
# sys.executable es la ruta absoluta al intérprete de Python que está ejecutando este script.
# Esto asegura que usemos el mismo entorno donde está instalado Streamlit.
command = [
    sys.executable, 
    "-m", 
    "streamlit", 
    "run", 
    app_file
]

print(f"Ejecutando comando: {' '.join(command)}")

# 3. Ejecutar el comando
try:
    # Usamos Popen para lanzar el proceso en una nueva ventana si es necesario,
    # aunque para Streamlit, se ejecutará en esta ventana y abrirá un navegador.
    process = subprocess.Popen(command, cwd=app_dir)
    process.wait() # Esperar a que el proceso de Streamlit termine (cuando se cierra la pestaña/servidor)
except FileNotFoundError:
    print("\nERROR: No se pudo encontrar 'streamlit'.")
    print("Asegúrate de que Streamlit está instalado en el entorno de Python correcto.")
    print("Puedes intentar ejecutar: pip install streamlit")
except Exception as e:
    print(f"\nOcurrió un error inesperado: {e}")
