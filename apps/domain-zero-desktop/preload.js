import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("dz", {
  pickRoot: () => ipcRenderer.invoke("pick-root"),
  verify: (root) => ipcRenderer.invoke("verify", root),
  quickstart: (root) => ipcRenderer.invoke("quickstart", root)
});
