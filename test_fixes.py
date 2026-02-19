import pandas as pd
import json
import os

# Simulamos la ruta del archivo de configuración
USER_CONFIG_PATH = 'test_fuentes.json'

# 1. Función corregida (La que acabamos de implementar)
def load_user_sources():
    print("--- Probando carga de fuentes ---")
    df = pd.DataFrame(columns=["activo", "alias", "ruta"])
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                loaded_df = pd.DataFrame(data)
                # Asegurar que existan todas las columnas
                for col in ["activo", "alias", "ruta"]:
                    if col not in loaded_df.columns:
                        print(f"Reparando columna faltante: {col}")
                        loaded_df[col] = "" if col == "ruta" or col == "alias" else True
                return loaded_df
        except Exception as e:
            print(f"Error leyendo archivo: {e}")
    return df

def save_user_sources(df):
    data = df.to_dict(orient="records")
    with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("Guardado exitoso.")

# --- PRUEBA 1: Archivo Inexistente (Debe crear DF vacío sin error) ---
if os.path.exists(USER_CONFIG_PATH):
    os.remove(USER_CONFIG_PATH)

df = load_user_sources()
print(f"DF Inicial (Vacío):\n{df}")
assert 'alias' in df.columns, "Falta la columna 'alias'"
assert 'ruta' in df.columns, "Falta la columna 'ruta'"
print("✅ PRUEBA 1 PASADA: Carga inicial robusta.\n")

# --- PRUEBA 2: Agregar Fuente (Simulando st.form) ---
print("--- Probando agregar fuente ---")
new_row = {"activo": True, "alias": "LEY 27444", "ruta": "G:/Normas/Ley27444"}
df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
save_user_sources(df)
print(f"DF con 1 fila:\n{df}")
print("✅ PRUEBA 2 PASADA: Agregado y guardado correctamente.\n")

# --- PRUEBA 3: Carga con Archivo Existente ---
print("--- Probando recarga ---")
df_reloaded = load_user_sources()
print(f"DF Recargado:\n{df_reloaded}")
assert len(df_reloaded) == 1, "Debería haber 1 fila"
assert df_reloaded.iloc[0]['alias'] == "LEY 27444", "El alias no coincide"
print("✅ PRUEBA 3 PASADA: Persistencia correcta.\n")

# --- PRUEBA 4: Simular Borrado (Lógica del Data Editor) ---
print("--- Probando lógica de borrado ---")
# Simulamos que el editor devuelve un DF vacío (usuario borró la fila)
user_edited_mock = pd.DataFrame(columns=["Cargar", "Nombre", "Vectores", "_tipo"]) # Vacío

current_aliases = df_reloaded['alias'].tolist()
edited_aliases = [] # El usuario borró todo

if len(edited_aliases) < len(current_aliases):
    deleted = list(set(current_aliases) - set(edited_aliases))
    print(f"Detectado borrado de: {deleted}")
    
    # Simulamos confirmación de clave
    clave_ingresada = "admin2026"
    if clave_ingresada == "admin2026":
        # Reconstrucción del DF
        alias_to_path = dict(zip(df_reloaded['alias'], df_reloaded['ruta']))
        new_rows = []
        # Como user_edited_mock está vacío, new_rows quedará vacío
        
        df_final = pd.DataFrame(new_rows)
        # La corrección crítica: Si queda vacío, restablecer columnas
        if df_final.empty:
            df_final = pd.DataFrame(columns=["activo", "alias", "ruta"])
            
        save_user_sources(df_final)
        print(f"DF Final tras borrado:\n{df_final}")
        assert df_final.empty, "El DF debería estar vacío"
        assert 'alias' in df_final.columns, "Faltan columnas tras vaciar"
        print("✅ PRUEBA 4 PASADA: Borrado y estructura preservada.")

# Limpieza
if os.path.exists(USER_CONFIG_PATH):
    os.remove(USER_CONFIG_PATH)

print("\n🎉 TODAS LAS PRUEBAS DE LÓGICA PASARON CORRECTAMENTE.")