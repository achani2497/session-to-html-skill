#!/usr/bin/env python3
"""Build a self-contained chat HTML from an OpenCode session export.

Standard library only -- no pip installs, no external tools.

Usage:
    python3 build_chat.py <session_export.json> [out.html] [--no-open]

Reads the JSON produced by `opencode export <session_id>`, keeps only the
visible `text` parts of user/assistant messages (drops reasoning, tool calls,
step markers and patches), renders a Markdown subset to HTML, fills
reference/chat-template.html and (by default) opens the result in the browser.
"""
import json
import html
import os
import re
import sys
import datetime
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "chat-template.html")


def esc(text):
    return html.escape(text or "", quote=False)


# --------------------------------------------------------------------------
# Minimal Markdown -> HTML (the subset that appears in OpenCode messages)
# --------------------------------------------------------------------------

def _inline(s):
    # s is already HTML-escaped
    s = re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               lambda m: '<a href="' + m.group(2) + '">' + m.group(1) + "</a>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", s)
    return s


def render_md(src):
    lines = (src or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        # fenced code block
        m = re.match(r"^\s*(```|~~~)(.*)$", line)
        if m:
            fence = m.group(1)
            i += 1
            code = []
            while i < n and not re.match(r"^\s*" + re.escape(fence) + r"\s*$", lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
            continue

        if not line.strip():
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, _inline(esc(m.group(2).strip())), lvl))
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            out.append("<hr />")
            i += 1
            continue

        # blockquote
        if re.match(r"^\s*>", line):
            buf = []
            while i < n and re.match(r"^\s*>", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + render_md("\n".join(buf)) + "</blockquote>")
            continue

        # table
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?[\s:|-]*$", lines[i + 1]) \
                and "-" in lines[i + 1]:
            def cells(row):
                row = row.strip()
                if row.startswith("|"):
                    row = row[1:]
                if row.endswith("|"):
                    row = row[:-1]
                return [c.strip() for c in row.split("|")]
            header = cells(line)
            i += 2
            rows = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(cells(lines[i]))
                i += 1
            t = "<table><thead><tr>" + "".join(
                "<th>" + _inline(esc(c)) + "</th>" for c in header) + "</tr></thead><tbody>"
            for r in rows:
                t += "<tr>" + "".join("<td>" + _inline(esc(c)) + "</td>" for c in r) + "</tr>"
            t += "</tbody></table>"
            out.append(t)
            continue

        # unordered list
        if re.match(r"^\s*[-*+]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join("<li>" + _inline(esc(x)) + "</li>" for x in items) + "</ul>")
            continue

        # ordered list
        if re.match(r"^\s*\d+[.)]\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join("<li>" + _inline(esc(x)) + "</li>" for x in items) + "</ol>")
            continue

        # paragraph (single newlines -> <br>, like nl2br)
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"^\s*(```|~~~|#{1,6}\s|>|[-*+]\s|\d+[.)]\s)", lines[i]) and not re.match(
                r"^\s*([-*_])(\s*\1){2,}\s*$", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + "<br />\n".join(_inline(esc(x)) for x in buf) + "</p>")

    return "\n".join(out)


# --------------------------------------------------------------------------

def ts(ms):
    try:
        return datetime.datetime.fromtimestamp(ms / 1000).strftime("%d/%m %H:%M")
    except Exception:
        return ""


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    no_open = "--no-open" in argv

    if not args:
        print(__doc__)
        return 2

    src = args[0]
    with open(src, encoding="utf-8") as fh:
        data = json.load(fh)

    info = data.get("info", {}) or {}
    messages = data.get("messages", []) or []

    bubbles = []
    for msg in messages:
        role = (msg.get("info") or {}).get("role")
        if role not in ("user", "assistant"):
            continue
        texts = [p.get("text", "") for p in msg.get("parts", [])
                 if p.get("type") == "text" and (p.get("text") or "").strip()]
        if not texts:
            continue
        who = "Vos" if role == "user" else "Asistente"
        created = (msg.get("info") or {}).get("time", {}).get("created", 0)
        body = render_md("\n\n".join(texts))
        bubbles.append(
            '    <div class="msg %s">\n'
            '      <div class="meta"><span class="who">%s</span><span class="time">%s</span></div>\n'
            '      <div class="bubble">%s</div>\n'
            '    </div>' % (role, who, ts(created), body)
        )

    model = info.get("model", {}) or {}
    model_str = ("%s/%s" % (model.get("providerID", ""), model.get("id", ""))).strip("/")
    title = info.get("title", "Conversación")
    subtitle = "%d mensajes · %s · %s" % (len(bubbles), model_str, ts(info.get("time", {}).get("created", 0)))

    with open(TEMPLATE, encoding="utf-8") as fh:
        tpl = fh.read()

    out_html = (tpl.replace("{{TITLE}}", html.escape(title, quote=False))
                   .replace("{{SUBTITLE}}", html.escape(subtitle, quote=False))
                   .replace("{{MESSAGES}}", "\n".join(bubbles)))

    out_path = args[1] if len(args) > 1 else "chat.html"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(out_html)

    print("OK -> %s (%d mensajes)" % (os.path.abspath(out_path), len(bubbles)))

    if not no_open:
        webbrowser.open("file://" + os.path.abspath(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
