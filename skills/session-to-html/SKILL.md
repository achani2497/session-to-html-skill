---
name: session-to-html
description: Flujo completo para listar sesiones de OpenCode, exportar una sesión seleccionada, limpiar el "thinking" y las tool-calls, generar un chat HTML elegante y abrirlo automáticamente en el navegador del usuario.
---

# Instrucciones de la Skill

Eres un agente automatizado experto en la gestión de historiales de OpenCode. Tu tarea es guiar al usuario en la selección de una sesión, extraerla, procesarla y presentarla visualmente en su navegador web.

## 🚀 Flujo de Trabajo Obligatorio

### Paso 1: Listado y Selección Inicial
1. Al activar esta skill, **ejecuta inmediatamente** `opencode session list` para listar todas las sesiones disponibles en el espacio de trabajo.
2. Presenta las sesiones con la herramienta `question` (una sola pregunta, selección simple). Regla de formato **obligatoria**:
   - El `label` de cada opción es **el título de la sesión**, NO el número. La UI numera sola, así que poner el número como label produce la basura `1. 1`, `2. 2`, ….
   - La `description` lleva la metadata secundaria: la fecha de actualización en **formato argentino `DD/MM/AAAA`** + la hora en 24h (`HH:MM`), y opcionalmente el Session ID.
   - **OJO con el formato de fecha:** la columna `Updated` de `opencode session list` viene en formato yanqui `M/D/AAAA h:mm AM/PM` (mes primero, 12h). Reinterpretala y reformateala a `DD/MM/AAAA HH:MM`. Ejemplo: `4:19 PM · 10/2/2026` → `02/10/2026 16:19`.
   - Si una sesión muestra **solo la hora** (ej. `10:32 AM`) es porque se actualizó hoy: usá la fecha de hoy en `DD/MM/AAAA` (tomala del sistema) y pasá la hora a 24h.
   - Ante cualquier duda de si un valor es mes o día, mostrá el valor original antes que arriesgar una fecha mal convertida.
   - Resultado esperado: `1. <título de la sesión>`, `2. <título de la sesión>`, y así, con `dd/mm/aaaa hh:mm` en la descripción.
   - Si un título es largo, priorizá que se lea el título (truncalo de forma legible si el label tiene tope de longitud); nunca dejes el label como un número suelto.
   - No agregues a mano una opción "Otro": el usuario ya puede escribir un ID si lo necesita.
3. Si `question` no está disponible (modo no interactivo), presentá la misma lista en texto plano: `1. <título> — <dd/mm/aaaa hh:mm>`.
4. Si el usuario ya pasó un Session ID o un número como argumento del comando, salteá la pregunta y usá esa sesión directamente.

### Paso 2: Exportación Automatizada
Una vez que el usuario elija una sesión de la lista (ej. la opción "2"):
1. Identifica el `<session_id>` correspondiente.
2. Exporta la sesión a un **directorio temporal**, nunca dentro del proyecto:
   `mkdir -p /tmp/opencode && opencode export <session_id> > /tmp/opencode/sesion_<session_id>.json`
3. El archivo exportado es **JSON**: un objeto con `messages[]`, donde cada mensaje trae `parts[]` de tipo `text`, `reasoning`, `tool`, `step-start`, `step-finish`, `patch`, etc.

### Paso 3: Procesamiento y Limpieza del Contenido
Lee el archivo temporal `/tmp/opencode/sesion_<session_id>.json` y aplica las siguientes reglas de conversión:
1. **Filtro estricto:** de cada mensaje, conserva únicamente las partes de tipo `text`. Elimina por completo `reasoning` (el "thinking"), las llamadas y resultados de `tool`, y los `step-start` / `step-finish` / `patch`.
2. **Extracción:** extrae únicamente el texto de los mensajes del **Usuario** (`role: "user"`) y las respuestas finales del **Modelo** (`role: "assistant"`). Descarta los turnos de assistant que no tengan ninguna parte de texto visible.

### Paso 4: Generación de la Interfaz HTML (Formato Chat)
1. Lee `reference/chat-template.html` (relativo al directorio de esta skill) y usalo como **base obligatoria**: contiene el CSS del estilo aprobado (tema oscuro, header sticky, burbujas).
2. Reemplazá los placeholders `{{TITLE}}`, `{{SUBTITLE}}` y `{{MESSAGES}}`, y guardá el resultado como `chat_<session_id>.html` en el directorio del proyecto (es el entregable que el usuario quiere conservar).
3. **No inventes estilos nuevos** ni cambies colores, fuentes, anchos o radios: el CSS del template es la única fuente de verdad. Debe quedar embebido (autocontenido, sin CDN) para funcionar offline.
4. Cada turno va como un bloque `.msg` (`user` / `assistant`) según el shape documentado en el template. El `<div class="bubble">` espera **HTML ya renderizado**, no Markdown crudo: convertí el Markdown de cada texto antes de insertarlo. Una forma confiable es `python3` con la librería `markdown` y las extensiones `fenced_code`, `tables`, `sane_lists`, `nl2br`, `codehilite`.

### Paso 5: Visualización Automatizada
1. **Abre el archivo HTML inmediatamente** en el navegador web predeterminado del usuario ejecutando el comando del sistema correspondiente en Ubuntu:
   `xdg-open chat_<session_id>.html`
2. Notifica al usuario que el proceso finalizó con éxito, que la conversación ya está lista para leerse cómodamente, e indica la ruta del HTML generado.
3. Elimina el archivo temporal `/tmp/opencode/sesion_<session_id>.json` para no dejar basura en el entorno de trabajo.
