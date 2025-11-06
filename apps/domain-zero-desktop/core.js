import fs from "fs/promises";
import path from "path";
import YAML from "yaml";

const CONFIG_PATH = "protocol.config.yaml";

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
  } catch (err) {
    console.error(`Config loading failed: ${err.message}`);
    errors.push(`Missing or invalid ${CONFIG_PATH}`);
  }

  // 2) Isolation: Check output files for Gojo mentions (dev-notes.md, security-review.md)
  const outputFiles = [
    path.join(root, ".protocol-state/dev-notes.md"),
    path.join(root, ".protocol-state/security-review.md")
  ];

  for (const f of outputFiles) {
    try {
      const txt = await fs.readFile(f, "utf8");
      // Skip if file is just template/empty
      if (txt.length > 100 && /gojo/i.test(txt)) {
        errors.push(`Isolation breach: "Gojo" mentioned in ${path.relative(root, f)}`);
      }
    } catch (err) {
      // File doesn't exist or can't be read - that's okay
    }
  }

  // 3) Workflow bindings present
  const workflowFiles = [
    { path: "protocol/YUUJI.md", name: "YUUJI.md" },
    { path: "protocol/MEGUMI.md", name: "MEGUMI.md" }
  ];

  for (const { path: filePath, name } of workflowFiles) {
    try {
      await fs.access(path.join(root, filePath));
    } catch {
      errors.push(`Missing protocol/${name}`);
    }
  }

  if (errors.length) {
    console.error("Protocol verify failed:\n - " + errors.join("\n - "));
    return { ok: false, errors };
  }
  console.log("Protocol verify passed");
  return { ok: true, errors: [] };
}

export async function initQuickstart(root) {
  const qs = path.join(root, "PROTOCOL_QUICKSTART.md");
  try {
    await fs.access(qs);
    return "Quick Start already present.";
  } catch {
    try {
      const content =
        "# Protocol Quick Start\n\n" +
        "1) Edit protocol.config.yaml (user, project, ai.defaultModels)\n" +
        "2) Run the Verify action from the desktop app\n" +
        "3) Invoke roles per protocol workflow\n";
      await fs.writeFile(qs, content, "utf8");
      return "Created PROTOCOL_QUICKSTART.md";
    } catch (writeErr) {
      throw new Error(`Failed to create quickstart file: ${writeErr.message}`);
    }
  }
}
