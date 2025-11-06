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
