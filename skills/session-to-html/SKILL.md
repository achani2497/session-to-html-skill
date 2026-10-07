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
1. Una vez que el usuario elija, identificá el `<session_id>` correspondiente.
2. Exportá la sesión a un **directorio temporal**, nunca dentro del proyecto:
   `mkdir -p "${TMPDIR:-/tmp}/opencode" && opencode export <session_id> > "${TMPDIR:-/tmp}/opencode/sesion_<session_id>.json"`
3. El archivo exportado es **JSON**: un objeto con `messages[]`, donde cada mensaje trae `parts[]` de tipo `text`, `reasoning`, `tool`, `step-start`, `step-finish`, `patch`, etc.

### Paso 3: Generación del HTML (script incluido, sin dependencias)
1. Corré el script que viene con esta skill (está en su carpeta `reference/`):
   `python3 ~/.config/opencode/skills/session-to-html/reference/build_chat.py "${TMPDIR:-/tmp}/opencode/sesion_<session_id>.json" "chat_<session_id>.html"`
   Si la skill está instalada en otra ruta, usá `<ruta-de-esta-skill>/reference/build_chat.py`.
2. El script ya hace todo el procesamiento:
   - conserva **solo las partes de tipo `text`** de los mensajes `user` y `assistant`; descarta `reasoning` (el "thinking"), `tool`, `step-start`/`step-finish` y `patch`;
   - convierte el Markdown de cada mensaje a HTML;
   - llena `reference/chat-template.html` y guarda `chat_<session_id>.html` en el directorio actual;
   - abre el HTML en el navegador por defecto. Pasale `--no-open` si NO querés que lo abra.
3. Requiere **únicamente `python3` (librería estándar)**. No hay que instalar nada más: nada de `pip`, nada de la librería `markdown`, nada de `xdg-open`.

### Paso 4: Estilo
- El diseño lo define íntegramente `reference/chat-template.html` (tema oscuro, header sticky, burbujas). **No inventes estilos** ni cambies colores, fuentes, anchos o radios.
- Si hay que cambiar el diseño, se edita el template — jamás un repositorio de HTML ya generado.

### Paso 5: Cierre
1. Avisá al usuario que el proceso terminó, indicá la ruta del `chat_<session_id>.html` y que la conversación ya está lista para leerse cómodamente.
2. Borrá el temporal: `rm -f "${TMPDIR:-/tmp}/opencode/sesion_<session_id>.json"`.

### Fallback (solo si no hay `python3`)
Si `python3` no está disponible, generá el HTML a mano: leé el JSON, quedate con las partes `text` de `user`/`assistant`, escapá el HTML del texto, convertí Markdown básico (títulos, listas, bloques de código, tablas, negrita) y llená `reference/chat-template.html`. Después abrí el archivo con la herramienta de apertura del sistema operativo (Linux `xdg-open`, macOS `open`, Windows `start`).
