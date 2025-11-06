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
  log(res.ok ? `✅ ${res.message}` : `❌ ${res.message}`);
  if (res.errors && res.errors.length > 0) {
    res.errors.forEach(err => log(`  • ${err}`));
  }
});

btnQuick.addEventListener("click", async () => {
  if (!rootPath) return;
  log("Creating Quick Start (if missing)...");
  const res = await window.dz.quickstart(rootPath);
  log(res.ok ? `✅ ${res.message}` : `❌ ${res.message}`);
});
