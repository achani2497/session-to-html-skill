#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const pkgRoot = path.resolve(__dirname, "..");

// OpenCode global config dir. Respect XDG_CONFIG_HOME like OpenCode does.
const configDir = process.env.XDG_CONFIG_HOME
  ? path.join(process.env.XDG_CONFIG_HOME, "opencode")
  : path.join(os.homedir(), ".config", "opencode");

// These are the folders OpenCode scans by default, so no config edit is needed.
const skillsDir = path.join(configDir, "skills");
const commandsDir = path.join(configDir, "commands");

const skillSrc = path.join(pkgRoot, "skills", "session-to-html");
const skillDest = path.join(skillsDir, "session-to-html");
const cmdSrc = path.join(pkgRoot, "commands", "session-to-html.md");
const cmdDest = path.join(commandsDir, "session-to-html.md");

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const from = path.join(src, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(from, to);
    else fs.copyFileSync(from, to);
  }
}

if (!fs.existsSync(skillSrc)) {
  console.error("No se encontró la skill en el paquete: " + skillSrc);
  process.exit(1);
}

copyDir(skillSrc, skillDest);
fs.mkdirSync(commandsDir, { recursive: true });
fs.copyFileSync(cmdSrc, cmdDest);

console.log("session-to-html-skill instalado:");
console.log("  skill   -> " + skillDest);
console.log("  command -> " + cmdDest);
console.log("");
console.log("Reiniciá OpenCode para que lo tome. Después: /session-to-html");
