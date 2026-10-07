---
description: Export an OpenCode session to a chat-style HTML file and open it in the browser
agent: gentle-orchestrator
---

Load the `session-to-html` skill and follow it exactly.

This workflow is interactive: list the available sessions, ask the user which one to export (unless they already named one), then export the session, strip the reasoning/tool noise, generate the chat HTML, and open it in the browser.

User input (may be a session id, number, or empty): $ARGUMENTS
