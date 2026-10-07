# session-to-html-skill

Instala la skill **`session-to-html`** y el comando **`/session-to-html`** en OpenCode,
sin editar configuración y sin asociarlo a ningún proyecto.

Lista tus sesiones de OpenCode, exportás una, y la convierte en un chat HTML
autocontenido (solo mensajes de usuario y asistente, sin *thinking* ni tool-calls)
que se abre en el navegador.

## Instalación

```bash
pnpm dlx session-to-html-skill
```

Copia la skill a `~/.config/opencode/skills/session-to-html/` y el comando a
`~/.config/opencode/commands/session-to-html.md` (respeta `XDG_CONFIG_HOME`).

Después **reiniciá OpenCode**.

> Alternativa con npm: `npx session-to-html-skill` (ver Seguridad).

## Uso

```
/session-to-html
```

## Seguridad

- Este paquete **no tiene scripts de instalación**: su `package.json` no declara
  ningún `scripts`, así que no ejecuta código al instalarse. El instalador corre
  **solo cuando lo invocás explícitamente**.
- Se recomienda **pnpm**: pnpm v10 **bloquea por defecto** los scripts de ciclo de vida
  de las dependencias. Con npm/npx esos scripts corren por defecto; si los usás, forzá
  `npm exec --ignore-scripts` o `npm config set ignore-scripts true`.

## Desinstalar

```bash
rm -rf ~/.config/opencode/skills/session-to-html
rm -f  ~/.config/opencode/commands/session-to-html.md
```

## Licencia

MIT
