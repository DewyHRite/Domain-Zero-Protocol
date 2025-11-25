/**
 * Domain Zero Protocol - Handoff Automation MCP Server
 *
 * @version 1.0.0
 * @description MCP server that automates agent handoffs by preparing context
 *              payloads and providing ready-to-execute invocation commands.
 *
 * Features:
 * - Automatic context extraction from project state
 * - Handoff trigger detection and validation
 * - Context payload generation per HANDOFF_SPECIFICATION.md
 * - Ready-to-execute agent invocation commands
 * - Handoff event logging for audit trail
 *
 * Usage:
 *   Configure in ~/.config/claude-code/mcp.json or .claude-code/mcp.json
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs/promises";
import * as path from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Maximum log file size (10MB) for log rotation
const MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024;

// Path validation utility to prevent path traversal attacks
async function validateProjectRoot(projectRoot) {
  if (!projectRoot || typeof projectRoot !== "string") {
    throw new Error("Invalid project root: path is required");
  }

  // Normalize and resolve the path
  const normalizedPath = path.resolve(projectRoot);

  // Use path.relative for robust path containment validation
  const cwd = process.cwd();
  const relativePath = path.relative(cwd, normalizedPath);

  // Reject any path that escapes the workspace, including absolute paths outside cwd
  // A path is safe if: relativePath is empty (same as cwd), doesn't start with "..", and isn't absolute
  if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
    throw new Error("Invalid project root: path must be within current workspace");
  }

  // Verify the path exists and is a directory
  try {
    const stats = await fs.stat(normalizedPath);
    if (!stats.isDirectory()) {
      throw new Error("Invalid project root: path is not a directory");
    }
  } catch (error) {
    if (error.code === "ENOENT") {
      throw new Error("Invalid project root: directory does not exist");
    }
    throw error;
  }

  // Resolve symlinks and verify final path is still within workspace
  try {
    const realPath = await fs.realpath(normalizedPath);
    const realRelativePath = path.relative(cwd, realPath);
    if (realRelativePath.startsWith("..") || path.isAbsolute(realRelativePath)) {
      throw new Error("Invalid project root: symlink points outside workspace");
    }
    return realPath;
  } catch (error) {
    // If realpath fails, return the normalized path (already validated)
    return normalizedPath;
  }
}

// Constants
const AGENTS = ["yuuji", "megumi", "nobara", "gojo"];
const TRIGGERS = {
  "@security-review": { source: "yuuji", target: "megumi" },
  "@user-review": { source: "yuuji", target: "gojo" },
  "@remediation-required": { source: "megumi", target: "yuuji" },
  "@re-review": { source: "yuuji", target: "megumi" },
  "@approved": { source: "megumi", target: "gojo" },
  "@brief-implementation": { source: "gojo", target: "yuuji" },
  "@brief-security": { source: "gojo", target: "megumi" },
  "@brief-design": { source: "gojo", target: "nobara" },
  "@implement-design": { source: "nobara", target: "yuuji" },
  "@security-ux-review": { source: "nobara", target: "megumi" },
  "@escalate": { source: "any", target: "gojo" },
};

// Context field extractors
const CONTEXT_EXTRACTORS = {
  files_modified: async (projectRoot) => {
    try {
      // Note: Returns [] on initial commit or if HEAD~1 doesn't exist
      // Using -- separator to prevent command injection via directory names
      const { stdout } = await execAsync("git diff --name-only HEAD~1 --", {
        cwd: projectRoot,
        encoding: "utf-8",
      });
      return stdout.trim().split("\n").filter(Boolean);
    } catch {
      return [];
    }
  },

  files_created: async (projectRoot) => {
    try {
      // Note: Returns [] on initial commit or if HEAD~1 doesn't exist
      // Using -- separator to prevent command injection via directory names
      const { stdout } = await execAsync("git diff --name-only --diff-filter=A HEAD~1 --", {
        cwd: projectRoot,
        encoding: "utf-8",
      });
      return stdout.trim().split("\n").filter(Boolean);
    } catch {
      return [];
    }
  },

  tier_level: async (projectRoot) => {
    try {
      const statePath = path.join(projectRoot, ".protocol-state", "project-state.json");
      const state = JSON.parse(await fs.readFile(statePath, "utf-8"));
      return state.current_tier || "standard";
    } catch {
      return "standard";
    }
  },

  implementation_scope: async (projectRoot) => {
    try {
      const notesPath = path.join(projectRoot, ".protocol-state", "dev-notes.md");
      const notes = await fs.readFile(notesPath, "utf-8");
      const scopeMatch = notes.match(/## Implementation Scope\s*\n([^\n#]+)/);
      return scopeMatch ? scopeMatch[1].trim() : "Feature implementation";
    } catch {
      return "Feature implementation";
    }
  },

  test_coverage: async (projectRoot) => {
    try {
      const coveragePath = path.join(projectRoot, "coverage", "coverage-summary.json");
      const coverage = JSON.parse(await fs.readFile(coveragePath, "utf-8"));
      return coverage.total || { statements: 0, branches: 0, functions: 0, lines: 0 };
    } catch {
      return { statements: 0, branches: 0, functions: 0, lines: 0 };
    }
  },

  security_findings: async (projectRoot) => {
    try {
      const reviewPath = path.join(projectRoot, ".protocol-state", "security-review.md");
      const review = await fs.readFile(reviewPath, "utf-8");
      const findings = [];
      // Limit match length to 500 chars to prevent ReDoS attacks
      const secIdRegex = /SEC-(\d+):\s*(.{0,500})/g;
      let match;
      while ((match = secIdRegex.exec(review)) !== null) {
        findings.push({
          sec_id: `SEC-${match[1]}`,
          description: match[2].trim(),
        });
      }
      return findings;
    } catch {
      return [];
    }
  },

  project_state: async (projectRoot) => {
    try {
      const statePath = path.join(projectRoot, ".protocol-state", "project-state.json");
      return JSON.parse(await fs.readFile(statePath, "utf-8"));
    } catch {
      return { status: "UNKNOWN" };
    }
  },
};

// Context fields per trigger
const TRIGGER_CONTEXT_FIELDS = {
  "@security-review": ["files_modified", "tier_level", "implementation_scope", "test_coverage"],
  "@user-review": ["files_modified", "implementation_scope"],
  "@remediation-required": ["security_findings"],
  "@re-review": ["files_modified", "security_findings"],
  "@approved": ["project_state"],
  "@brief-implementation": ["project_state", "tier_level"],
  "@brief-security": ["project_state", "security_findings"],
  "@brief-design": ["project_state"],
  "@implement-design": ["files_modified", "tier_level"],
  "@security-ux-review": ["files_modified"],
  "@escalate": ["project_state"],
};

// Server setup
const server = new Server(
  {
    name: "domain-zero-handoff",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Tool: prepare_handoff
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "prepare_handoff",
        description:
          "Prepares a handoff context payload for agent transition. Returns the context payload and ready-to-execute invocation command.",
        inputSchema: {
          type: "object",
          properties: {
            trigger: {
              type: "string",
              description: "The handoff trigger keyword (e.g., @security-review)",
              enum: Object.keys(TRIGGERS),
            },
            source_agent: {
              type: "string",
              description: "The agent initiating the handoff",
              enum: AGENTS,
            },
            project_root: {
              type: "string",
              description: "Path to the project root directory",
            },
            additional_context: {
              type: "object",
              description: "Additional context to include in the handoff payload",
            },
          },
          required: ["trigger", "source_agent", "project_root"],
        },
      },
      {
        name: "get_invocation_command",
        description:
          "Returns the ready-to-execute command to invoke the target agent with context.",
        inputSchema: {
          type: "object",
          properties: {
            target_agent: {
              type: "string",
              description: "The target agent to invoke",
              enum: AGENTS,
            },
            tier: {
              type: "string",
              description: "The tier level for the invocation",
              enum: ["rapid", "standard", "critical"],
            },
            task_description: {
              type: "string",
              description: "Brief description of the task for the target agent",
            },
          },
          required: ["target_agent"],
        },
      },
      {
        name: "log_handoff_event",
        description: "Logs a handoff event to the project state for audit trail.",
        inputSchema: {
          type: "object",
          properties: {
            project_root: {
              type: "string",
              description: "Path to the project root directory",
            },
            event: {
              type: "object",
              description: "The handoff event to log",
              properties: {
                source_agent: { type: "string" },
                target_agent: { type: "string" },
                trigger: { type: "string" },
                status: { type: "string", enum: ["pending", "completed", "failed"] },
              },
            },
          },
          required: ["project_root", "event"],
        },
      },
      {
        name: "list_pending_handoffs",
        description: "Lists all pending handoffs for the current project.",
        inputSchema: {
          type: "object",
          properties: {
            project_root: {
              type: "string",
              description: "Path to the project root directory",
            },
          },
          required: ["project_root"],
        },
      },
      {
        name: "validate_handoff",
        description: "Validates that a handoff is allowed between source and target agents.",
        inputSchema: {
          type: "object",
          properties: {
            trigger: {
              type: "string",
              description: "The handoff trigger keyword",
            },
            source_agent: {
              type: "string",
              description: "The source agent",
            },
          },
          required: ["trigger", "source_agent"],
        },
      },
    ],
  };
});

// Tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name } = request.params;
  const args = request.params.arguments ?? {};

  switch (name) {
    case "prepare_handoff": {
      const { trigger, source_agent, project_root, additional_context } = args;

      // Validate project root path
      let validatedProjectRoot;
      try {
        validatedProjectRoot = await validateProjectRoot(project_root);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: error.message }, null, 2),
            },
          ],
        };
      }

      // Validate trigger
      if (!TRIGGERS[trigger]) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: `Invalid trigger: ${trigger}`, valid_triggers: Object.keys(TRIGGERS) },
                null,
                2
              ),
            },
          ],
        };
      }

      const triggerInfo = TRIGGERS[trigger];

      // Validate source agent
      if (triggerInfo.source !== "any" && triggerInfo.source !== source_agent) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  error: `Invalid source agent for trigger ${trigger}`,
                  expected: triggerInfo.source,
                  received: source_agent,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      // Extract context fields
      const contextFields = TRIGGER_CONTEXT_FIELDS[trigger] || [];
      const context = {};

      for (const field of contextFields) {
        if (CONTEXT_EXTRACTORS[field]) {
          context[field] = await CONTEXT_EXTRACTORS[field](validatedProjectRoot);
        }
      }

      // Merge additional context with prototype pollution protection
      if (additional_context && typeof additional_context === "object") {
        const safeContext = Object.entries(additional_context)
          .filter(([key]) => key !== "__proto__" && key !== "constructor" && key !== "prototype")
          .reduce((obj, [key, value]) => ({ ...obj, [key]: value }), {});
        Object.assign(context, safeContext);
      }

      // Generate event ID
      const eventId = `HO-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;

      // Generate invocation command
      const targetAgent = triggerInfo.target;
      const invocationCommand = `Read ${targetAgent}.agent.md and review the handoff context`;

      const result = {
        event_id: eventId,
        timestamp: new Date().toISOString(),
        source_agent,
        target_agent: targetAgent,
        trigger,
        context,
        invocation_command: invocationCommand,
        status: "pending",
      };

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }

    case "get_invocation_command": {
      const { target_agent, tier, task_description } = args;

      let command = `Read ${target_agent}.agent.md`;

      if (tier && tier !== "standard") {
        command += ` --tier ${tier}`;
      }

      if (task_description) {
        command += ` and ${task_description}`;
      }

      const result = {
        target_agent,
        tier: tier || "standard",
        command,
        copy_paste_ready: true,
        note: "Copy this command and paste it to invoke the target agent with proper context.",
      };

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }

    case "log_handoff_event": {
      const { project_root, event } = args;

      // Validate project root path
      let validatedProjectRoot;
      try {
        validatedProjectRoot = await validateProjectRoot(project_root);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: error.message }, null, 2),
            },
          ],
        };
      }

      try {
        const handoffLogPath = path.join(validatedProjectRoot, ".protocol-state", "handoff-log.json");

        let log = [];
        try {
          const logContent = await fs.readFile(handoffLogPath, "utf-8");
          log = JSON.parse(logContent);

          // Check log file size and rotate if needed
          const stats = await fs.stat(handoffLogPath);
          if (stats.size > MAX_LOG_SIZE_BYTES) {
            // Archive old log and start fresh
            const archivePath = handoffLogPath.replace(".json", `-${Date.now()}.archive.json`);
            await fs.rename(handoffLogPath, archivePath);
            log = [];
          }
        } catch {
          // File doesn't exist, start fresh
        }

        const logEntry = {
          event_id: `HO-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
          timestamp: new Date().toISOString(),
          ...event,
        };

        log.push(logEntry);

        // Ensure directory exists
        await fs.mkdir(path.dirname(handoffLogPath), { recursive: true });
        await fs.writeFile(handoffLogPath, JSON.stringify(log, null, 2));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: true, event_id: logEntry.event_id }, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: error.message }, null, 2),
            },
          ],
        };
      }
    }

    case "list_pending_handoffs": {
      const { project_root } = args;

      // Validate project root path
      let validatedProjectRoot;
      try {
        validatedProjectRoot = await validateProjectRoot(project_root);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: error.message }, null, 2),
            },
          ],
        };
      }

      try {
        const handoffLogPath = path.join(validatedProjectRoot, ".protocol-state", "handoff-log.json");
        const log = JSON.parse(await fs.readFile(handoffLogPath, "utf-8"));
        const pending = log.filter((entry) => entry.status === "pending");

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ pending_handoffs: pending, count: pending.length }, null, 2),
            },
          ],
        };
      } catch {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ pending_handoffs: [], count: 0 }, null, 2),
            },
          ],
        };
      }
    }

    case "validate_handoff": {
      const { trigger, source_agent } = args;

      if (!TRIGGERS[trigger]) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { valid: false, error: `Unknown trigger: ${trigger}` },
                null,
                2
              ),
            },
          ],
        };
      }

      const triggerInfo = TRIGGERS[trigger];
      const isValid = triggerInfo.source === "any" || triggerInfo.source === source_agent;

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                valid: isValid,
                trigger,
                source_agent,
                expected_source: triggerInfo.source,
                target_agent: triggerInfo.target,
                context_fields: TRIGGER_CONTEXT_FIELDS[trigger] || [],
              },
              null,
              2
            ),
          },
        ],
      };
    }

    default:
      return {
        content: [{ type: "text", text: JSON.stringify({ error: `Unknown tool: ${name}` }, null, 2) }],
      };
  }
});

// Resources handler
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "handoff://triggers",
        name: "Available Handoff Triggers",
        description: "List of all valid handoff triggers and their source/target agents",
        mimeType: "application/json",
      },
      {
        uri: "handoff://context-fields",
        name: "Context Field Definitions",
        description: "Available context fields for handoff payloads",
        mimeType: "application/json",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  switch (uri) {
    case "handoff://triggers":
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(TRIGGERS, null, 2),
          },
        ],
      };

    case "handoff://context-fields":
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(TRIGGER_CONTEXT_FIELDS, null, 2),
          },
        ],
      };

    default:
      throw new Error(`Unknown resource: ${uri}`);
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Domain Zero Handoff MCP Server running on stdio");
}

main().catch(console.error);
