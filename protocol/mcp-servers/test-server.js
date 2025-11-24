/**
 * Test script for Domain Zero Handoff MCP Server
 *
 * This script tests the MCP server by sending JSON-RPC messages
 * and verifying responses.
 */

import { spawn } from "child_process";
import * as path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Colors for output
const GREEN = "\x1b[32m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const RESET = "\x1b[0m";

function log(color, prefix, message) {
  console.log(`${color}[${prefix}]${RESET} ${message}`);
}

// JSON-RPC message helper
function createMessage(method, params = {}, id = 1) {
  return JSON.stringify({
    jsonrpc: "2.0",
    method,
    params,
    id,
  }) + "\n";
}

async function runTests() {
  log(YELLOW, "TEST", "Starting MCP Handoff Server tests...\n");

  const serverPath = path.join(__dirname, "handoff-server.js");
  const server = spawn("node", [serverPath], {
    stdio: ["pipe", "pipe", "pipe"],
  });

  let responseBuffer = "";
  const responses = [];

  server.stdout.on("data", (data) => {
    responseBuffer += data.toString();
    // Try to parse complete JSON-RPC responses
    const lines = responseBuffer.split("\n");
    for (let i = 0; i < lines.length - 1; i++) {
      try {
        const response = JSON.parse(lines[i]);
        responses.push(response);
      } catch {
        // Not a valid JSON line, skip
      }
    }
    responseBuffer = lines[lines.length - 1];
  });

  server.stderr.on("data", (data) => {
    const msg = data.toString().trim();
    if (msg.includes("running")) {
      log(GREEN, "SERVER", msg);
    }
  });

  // Wait for server to start
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 1: List tools
  log(YELLOW, "TEST 1", "Listing available tools...");
  server.stdin.write(createMessage("tools/list", {}, 1));
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Test 2: Validate handoff
  log(YELLOW, "TEST 2", "Validating @security-review handoff...");
  server.stdin.write(
    createMessage(
      "tools/call",
      {
        name: "validate_handoff",
        arguments: {
          trigger: "@security-review",
          source_agent: "yuuji",
        },
      },
      2
    )
  );
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Test 3: Get invocation command
  log(YELLOW, "TEST 3", "Getting invocation command for megumi...");
  server.stdin.write(
    createMessage(
      "tools/call",
      {
        name: "get_invocation_command",
        arguments: {
          target_agent: "megumi",
          tier: "standard",
          task_description: "review authentication implementation",
        },
      },
      3
    )
  );
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Test 4: List resources
  log(YELLOW, "TEST 4", "Listing available resources...");
  server.stdin.write(createMessage("resources/list", {}, 4));
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Test 5: Read triggers resource
  log(YELLOW, "TEST 5", "Reading handoff://triggers resource...");
  server.stdin.write(
    createMessage("resources/read", { uri: "handoff://triggers" }, 5)
  );
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Wait for all responses
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Clean up
  server.kill();

  // Print results
  console.log("\n" + "=".repeat(60));
  log(GREEN, "RESULTS", `Received ${responses.length} responses\n`);

  let passed = 0;
  let failed = 0;

  for (const response of responses) {
    if (response.error) {
      log(RED, `FAIL`, `ID ${response.id}: ${response.error.message}`);
      failed++;
    } else {
      log(GREEN, `PASS`, `ID ${response.id}: Success`);

      // Print some details
      if (response.id === 1 && response.result?.tools) {
        console.log(`       Tools available: ${response.result.tools.map(t => t.name).join(", ")}`);
      }
      if (response.id === 2 && response.result?.content?.[0]?.text) {
        const data = JSON.parse(response.result.content[0].text);
        console.log(`       Valid: ${data.valid}, Target: ${data.target_agent}`);
      }
      if (response.id === 3 && response.result?.content?.[0]?.text) {
        const data = JSON.parse(response.result.content[0].text);
        console.log(`       Command: "${data.command}"`);
      }
      if (response.id === 4 && response.result?.resources) {
        console.log(`       Resources: ${response.result.resources.map(r => r.uri).join(", ")}`);
      }
      passed++;
    }
  }

  console.log("\n" + "=".repeat(60));
  log(passed === responses.length ? GREEN : RED, "SUMMARY",
      `${passed} passed, ${failed} failed out of ${responses.length} tests`);

  if (passed === responses.length && responses.length > 0) {
    log(GREEN, "SUCCESS", "MCP Handoff Server is working correctly!");
  } else if (responses.length === 0) {
    log(RED, "ERROR", "No responses received - server may have failed to start");
  } else {
    log(RED, "ERROR", "Some tests failed");
  }

  process.exit(failed > 0 ? 1 : 0);
}

runTests().catch((err) => {
  log(RED, "ERROR", err.message);
  process.exit(1);
});
