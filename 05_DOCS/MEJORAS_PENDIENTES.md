# Mejoras Pendientes — Sistema de Consulta Normativa

> **Creado:** 24 de Febrero 2026
> **Estado:** Pendiente de implementación
> **Archivo a modificar (salvo indicación):** `01_APP_CORE/app_interfaz.py`

---

## Mejora 1 — Streaming de R1

**Estado:** ✅ Implementada (24-Feb-2026)
**Prioridad:** Alta
**Dificultad:** Baja (~1 hora)

### Problema
R1 tarda 20-40 segundos generando la respuesta. El usuario ve un spinner congelado y no sabe si el sistema está procesando o se colgó.

### Solución
Activar `"stream": true` en la llamada a DeepSeek R1 y usar `st.write_stream()` de Streamlit para mostrar la respuesta carácter por carácter mientras se genera.

### Cambios necesarios
- En `consultar_deepseek()`: agregar `"stream": True` al payload y cambiar el manejo de la respuesta para iterar sobre chunks SSE.
- En el handler principal: reemplazar `st.markdown(respuesta)` por `st.write_stream(stream_generator)`.

### Referencia técnica
```python
# DeepSeek soporta streaming estándar OpenAI-compatible
payload["stream"] = True
response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, stream=True)
for line in response.iter_lines():
    if line.startswith(b"data: "):
        chunk = json.loads(line[6:])
        delta = chunk["choices"][0]["delta"].get("content", "")
        yield delta  # Streamlit st.write_stream() consume este generador
```

---

## Mejora 2 — Verificación de Citas (Anti-alucinación)

**Estado:** ✅ Implementada (24-Feb-2026)
**Prioridad:** Alta
**Dificultad:** Media (~2-3 horas)

### Problema
R1 puede citar "Art. 64.4" con contenido ligeramente distinto al texto real, o inventar un número de artículo. En un sistema legal esto es crítico — una cita incorrecta puede llevar a decisiones erróneas.

### Solución
Post-proceso que extrae todas las citas de la respuesta de R1 (`Art. N`, `artículo N`, `numeral N.N`) y las cruza contra los chunks recuperados. Las citas que no aparecen en ningún chunk se marcan con ⚠️.

### Cambios necesarios
- Nueva función `verificar_citas(respuesta, chunks)` que:
  1. Extrae citas con regex: `r'[Aa]rt[íi]culo[s]?\s+(\d+[\.\d]*)'`
  2. Para cada cita, busca si algún chunk contiene ese número de artículo
  3. Retorna lista de citas verificadas y no verificadas
- En el handler: llamar a `verificar_citas()` después de recibir respuesta de R1
- Mostrar un pequeño bloque de advertencia si hay citas no verificadas

### Ejemplo de output esperado
```
✅ Citas verificadas en contexto: Art. 304, Art. 306, Art. 309
⚠️ No encontradas en contexto (verificar manualmente): Art. 64.4
```

---

## Mejora 3 — Memoria de Sesión Resumida

**Estado:** ✅ Implementada (24-Feb-2026)
**Prioridad:** Media
**Dificultad:** Media (~2 horas)

### Problema
En conversaciones largas (5+ turnos), el agente solo recibe los últimos 2 turnos crudos. Si en el turno 1 se establece contexto importante ("estoy evaluando una licitación LP-001-2025") y en el turno 6 se pregunta "¿y los plazos?", el agente puede perder ese contexto inicial.

### Solución
Mantener un resumen acumulativo de la sesión en `st.session_state.session_summary`. Después de cada respuesta, Chat actualiza el resumen con los puntos clave discutidos. El agente recibe el resumen (compacto) en lugar de mensajes crudos.

### Cambios necesarios
- Nueva función `actualizar_resumen_sesion(resumen_anterior, ultimo_turno)` usando deepseek-chat (rápido/barato).
- Nuevo campo en session_state: `session_summary = ""`
- En `agentic_consultar_deepseek()`: pasar el resumen como contexto del sistema en lugar de los mensajes crudos del historial.
- Botón "🧹 Limpiar Historial" también limpia el resumen.

### Referencia técnica
```python
# El resumen se construye así:
prompt_resumen = f"""Resume en 3-5 líneas los temas clave discutidos:
RESUMEN ANTERIOR: {resumen_anterior}
NUEVO TURNO:
Usuario: {ultimo_user}
Asistente: {ultima_respuesta[:300]}
RESUMEN ACTUALIZADO:"""
```

---

## Orden de implementación recomendado

| # | Mejora | Impacto | Esfuerzo | Implementar cuando... |
|---|--------|---------|----------|----------------------|
| 1 | Streaming R1 | ⭐⭐⭐ Visual e inmediato | Bajo | Primera oportunidad |
| 2 | Verificación citas | ⭐⭐⭐ Crítico legal | Medio | Antes de uso intensivo |
| 3 | Memoria sesión | ⭐⭐ Conversaciones largas | Medio | Si se usan sesiones de 5+ turnos |
