# Domain Zero Desktop Wrapper (Electron)

A minimal Electron desktop app for running Domain Zero actions outside of VS Code. It wraps two core actions:
- Verify Protocol: checks isolation, workflow bindings, and config presence
- Quick Start: generates a short Quick Start file if missing

This guide includes copy-paste templates and Windows-friendly steps.

## What you get
- Desktop UI to pick any repo folder and run Verify/Quick Start
- Portable structure you can package as an installer (.exe)
- A tiny core module you can later share with a CLI (dz) or server

## Prerequisites
- Node.js LTS (18+)
- Git (optional, for versioning)
- Windows PowerShell or Terminal

## Recommended layout
Create the desktop app inside the repo:

```
apps/
  domain-zero-desktop/
    package.json
    main.js
    preload.js
    core.js
    renderer/
      index.html
      renderer.js
```

> You can place it elsewhere; the app lets you pick any target repo root at runtime.

---

## Files (copy/paste)

### package.json
```json
{
  "name": "domain-zero-desktop",
  "version": "0.1.0",
  "private": true,
  "description": "Desktop wrapper for Domain Zero protocol",
  "main": "main.js",
  "type": "module",
  "scripts": {
    "start": "electron .",
    "pack": "electron-builder --dir",
    "dist": "electron-builder"
  },
  "dependencies": {
    "electron-updater": "^6.3.9",
    "glob": "^10.3.10",
    "yaml": "^2.5.1"
  },
  "devDependencies": {
    "electron": "^31.3.1",
    "electron-builder": "^24.13.3"
  },
  "build": {
    "appId": "com.domainzero.desktop",
    "productName": "Domain Zero",
    "win": {
      "target": ["nsis"],
      "artifactName": "DomainZero-Setup-${version}.exe"
    },
    "files": [
      "main.js",
      "preload.js",
      "renderer/**/*",
      "core.js",
      "package.json"
    ],
    "asar": true
  }
}
```

### main.js
```js
import { app, BrowserWindow, ipcMain, dialog } from "electron";
import path from "path";
import { fileURLToPath } from "url";
import { verifyProtocol, initQuickstart } from "./core.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 900,
    height: 650,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true
    }
  });

  win.loadFile(path.join(__dirname, "renderer", "index.html"));
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// IPC handlers
ipcMain.handle("pick-root", async () => {
  const result = await dialog.showOpenDialog(win, {
    title: "Select repository root",
    properties: ["openDirectory"]
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  return result.filePaths[0];
});

ipcMain.handle("verify", async (_evt, root) => {
  try {
    const ok = await verifyProtocol(root);
    return { ok, message: ok ? "Protocol verify passed" : "Protocol verify failed. See errors above." };
  } catch (e) {
    return { ok: false, message: String(e?.message || e) };
  }
});

ipcMain.handle("quickstart", async (_evt, root) => {
  try {
    const msg = await initQuickstart(root);
    return { ok: true, message: msg };
  } catch (e) {
    return { ok: false, message: String(e?.message || e) };
  }
});
```

### preload.js
```js
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("dz", {
  pickRoot: () => ipcRenderer.invoke("pick-root"),
  verify: (root) => ipcRenderer.invoke("verify", root),
  quickstart: (root) => ipcRenderer.invoke("quickstart", root)
});
```

### renderer/index.html
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Domain Zero</title>
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'">
    <style>
      body { font-family: system-ui, Segoe UI, Arial; margin: 16px; }
      .row { margin: 12px 0; }
      #rootPath { font-weight: 600; }
      #log { white-space: pre-wrap; background: #0b0b0b; color: #e6e6e6; padding: 12px; border-radius: 6px; height: 300px; overflow: auto; }
      button { padding: 8px 12px; margin-right: 8px; }
    </style>
  </head>
  <body>
    <h2>Domain Zero Desktop</h2>
    <div class="row">
      <button id="btnPick">Select Repo...</button>
      <span>Root: <span id="rootPath">(none)</span></span>
    </div>
    <div class="row">
      <button id="btnVerify" disabled>Verify Protocol</button>
      <button id="btnQuickstart" disabled>Create Quick Start</button>
    </div>
    <div class="row">
      <div id="log" aria-live="polite"></div>
    </div>
    <script type="module" src="./renderer.js"></script>
  </body>
</html>
```

### renderer/renderer.js
```js
const btnPick = document.getElementById("btnPick");
const btnVerify = document.getElementById("btnVerify");
const btnQuick = document.getElementById("btnQuickstart");
const rootPathEl = document.getElementById("rootPath");
const logEl = document.getElementById("log");

let rootPath = null;

function log(msg) {
  const ts = new Date().toLocaleTimeString();
  logEl.textContent += `[${ts}] ${msg}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

btnPick.addEventListener("click", async () => {
  const picked = await window.dz.pickRoot();
  if (!picked) return;
  rootPath = picked;
  rootPathEl.textContent = rootPath;
  btnVerify.disabled = false;
  btnQuick.disabled = false;
  log(`Selected root: ${rootPath}`);
});

btnVerify.addEventListener("click", async () => {
  if (!rootPath) return;
  log("Running verify...");
  const res = await window.dz.verify(rootPath);
  log(res.message);
});

btnQuick.addEventListener("click", async () => {
  if (!rootPath) return;
  log("Creating Quick Start (if missing)...");
  const res = await window.dz.quickstart(rootPath);
  log(res.message);
});
```

### core.js
```js
import fs from "fs/promises";
import path from "path";
import YAML from "yaml";
import glob from "glob";

const CONFIG_PATH = "domain_zero/protocol.config.yaml";

async function loadConfig(root) {
  const p = path.join(root, CONFIG_PATH);
  const raw = await fs.readFile(p, "utf8");
  return YAML.parse(raw);
}

export async function verifyProtocol(root) {
  const errors = [];

  // 1) Config presence
  try {
    await loadConfig(root);
  } catch {
    errors.push(`Missing or invalid ${CONFIG_PATH}`);
  }

  // 2) Isolation: Yuuji/Megumi files must not mention Gojo
  const yFiles = glob.sync(path.join(root, "domain_zero/**/*yuuji*.md").replace(/\\/g, "/"));
  const mFiles = glob.sync(path.join(root, "domain_zero/**/*megumi*.md").replace(/\\/g, "/"));
  for (const f of [...yFiles, ...mFiles]) {
    const txt = await fs.readFile(f, "utf8");
    if (/gojo/i.test(txt)) {
      errors.push(`Isolation breach: "Gojo" mentioned in ${path.relative(root, f)}`);
    }
  }

  // 3) Workflow bindings present
  try {
    await fs.access(path.join(root, "domain_zero/bindings/workflow.md"));
  } catch {
    errors.push("Missing domain_zero/bindings/workflow.md");
  }

  if (errors.length) {
    const msg = "Protocol verify failed:\n - " + errors.join("\n - ");
    console.error(msg);
    return false;
  }
  console.log("Protocol verify passed");
  return true;
}

export async function initQuickstart(root) {
  const qs = path.join(root, "PROTOCOL_QUICKSTART.md");
  try {
    await fs.access(qs);
    return "Quick Start already present.";
  } catch {
    const content =
      "# Protocol Quick Start\n\n" +
      "1) Edit domain_zero/protocol.config.yaml (user, project, ai.defaultModels)\n" +
      "2) Run the Verify action from the desktop app\n" +
      "3) Invoke roles per domain_zero/bindings/workflow.md\n";
    await fs.writeFile(qs, content, "utf8");
    return "Created PROTOCOL_QUICKSTART.md";
  }
}
```

---

## How to run (Windows PowerShell)

```powershell
# 1) Create folders
mkdir "apps/domain-zero-desktop" -Force | Out-Null
mkdir "apps/domain-zero-desktop/renderer" -Force | Out-Null

# 2) Save the files above into the paths shown

# 3) Install & start
cd "apps/domain-zero-desktop"
npm install
npm start
```

This opens the desktop app. Click "Select Repo..." and choose your repository root. Then use "Verify Protocol" or "Create Quick Start".

## Package as an installer (optional)
```powershell
cd "apps/domain-zero-desktop"
npm run dist
# Output: dist/DomainZero-Setup-0.1.0.exe
```

## Security: Snyk at inception
Per `.github/instructions/snyk_rules.instructions.md`, scan first-party code you add:
```powershell
npm i -g snyk
snyk auth
cd "apps/domain-zero-desktop"
snyk code test
```
If issues are found, apply fixes, then rerun `snyk code test` until clean.

## Next steps
- Share core with a CLI (create a `dz-core` folder or package and import in both CLI and desktop)
- Add a web server mode later (Express/FastAPI) reusing the same `core.js`
- Extend `verifyProtocol` to check output headers and config completeness
- Wire a GitHub Action to run a CLI `dz verify` on PRs
