import sys
import os
import json

# Agregar la ruta del sistema de consultas
sys.path.insert(0, r'G:\Mi unidad\01_BASE_NORMATIVA\000_CONSULTAS')

def verificar_configuracion():
    """
    Verifica que la configuración del sistema esté correcta
    """
    print("=== VERIFICACIÓN DE CONFIGURACIÓN DEL SISTEMA ===\n")
    
    # Cargar configuración
    config_path = r'G:\Mi unidad\01_BASE_NORMATIVA\000_CONSULTAS\config.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✓ Archivo de configuración cargado correctamente")
    except Exception as e:
        print(f"✗ Error al cargar el archivo de configuración: {e}")
        return False
    
    # Verificar que se haya agregado la entrada de directivas
    nombres_indices = [idx['nombre'] for idx in config['indices']]
    
    if 'Directivas OECE 2025-2026' in nombres_indices:
        print("✓ Entrada de 'Directivas OECE 2025-2026' encontrada en la configuración")
    else:
        print("✗ Entrada de 'Directivas OECE 2025-2026' NO encontrada en la configuración")
        return False
    
    # Verificar que existan los archivos físicos
    base_path = r'G:\Mi unidad\01_BASE_NORMATIVA\002_Directivas_oece_2025\embeddings_unificados'
    
    archivos_requeridos = [
        'directivas_oece_2025_2026.index',
        'chunks.json',
        'metadata.pkl'
    ]
    
    print(f"\nVerificando archivos en: {base_path}")
    
    for archivo in archivos_requeridos:
        ruta_completa = os.path.join(base_path, archivo)
        if os.path.exists(ruta_completa):
            print(f"✓ {archivo} - EXISTE")
        else:
            print(f"✗ {archivo} - NO EXISTE")
            return False
    
    print(f"\n✓ Todos los archivos requeridos existen")
    
    # Mostrar resumen
    print(f"\n--- RESUMEN DE ÍNDICES ACTIVOS ---")
    for i, indice in enumerate(config['indices'], 1):
        print(f"{i}. {indice['nombre']}")
        print(f"   Descripción: {indice['descripcion']}")
        print(f"   Ruta índice: {indice['ruta_indice']}")
        print(f"   Ruta chunks: {indice['ruta_chunks']}")
        print(f"   Ruta metadata: {indice['ruta_metadata']}")
        print()
    
    print("✓ Verificación completada exitosamente")
    print("✓ El sistema está listo para usar con las nuevas directivas OECE")
    
    return True

if __name__ == "__main__":
    success = verificar_configuracion()
    
    if success:
        print("\n🎉 ¡TODO LISTO! Las directivas OECE 2025-2026 están integradas correctamente al sistema.")
        print("\nPara iniciar el sistema de consultas, ejecuta: 00_START.bat")
    else:
        print("\n❌ Hubo errores en la verificación. Revisa los mensajes anteriores.")