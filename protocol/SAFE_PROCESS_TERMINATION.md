# Safe Process Termination Guidelines
<!-- [CORE FILE] - Domain Zero Protocol v8.8.0 -->

**Version**: 1.0.0
**Created**: 2025-12-16
**Purpose**: Prevent Claude Code self-termination when managing Node.js processes
**Related Issue**: Claude Code GitHub Issue #3068

---

## 🚨 CRITICAL: Prevent Self-Termination

**Claude Code runs on Node.js runtime.** Using broad process termination commands will kill Claude Code itself, terminating your development environment and losing unsaved work.

**This applies to**:
- VS Code + Claude Code extension
- Any Electron-based IDE running Claude Code
- All platforms: Windows, macOS, Linux

---

## ❌ FORBIDDEN COMMANDS (Never Use These)

**NEVER execute these commands under any circumstances:**

### Linux/macOS Forbidden Commands:
```bash
# ❌ FORBIDDEN - Kills ALL Node.js processes including Claude Code
pkill node
pkill -f node
killall node
pkill -9 node
killall -9 node

# ❌ FORBIDDEN - Pattern matching that's too broad
pkill -f "node"  # Matches everything with "node" in command line
```

### Windows PowerShell Forbidden Commands:
```powershell
# ❌ FORBIDDEN - Kills ALL Node.js processes including Claude Code
Get-Process -Name node | Stop-Process -Force
Stop-Process -Name node -Force
taskkill /IM node.exe /F

# ❌ FORBIDDEN - Kills all processes matching pattern
Get-Process | Where-Object {$_.Name -eq "node"} | Stop-Process -Force
```

### Why These Are Dangerous:
1. **Claude Code Process**: Runs on Node.js - gets killed immediately
2. **VS Code Process**: Electron-based (Node.js) - also gets killed
3. **All Node Tools**: npm, yarn, TypeScript servers - everything dies
4. **Data Loss**: Unsaved work, open files, terminal sessions all lost
5. **Session Loss**: Complete development environment termination

---

## ✅ SAFE ALTERNATIVES

### 1. Port-Specific Termination (Recommended)

**Use this when**: You know the port number the process is using.

#### Linux/macOS:
```bash
# Basic port-specific kill
lsof -ti :3000 | xargs kill -9

# With error handling and confirmation
PORT=3000
PID=$(lsof -ti :$PORT)
if [ ! -z "$PID" ]; then
  echo "Killing process on port $PORT (PID: $PID)"
  kill -9 $PID
  echo "✓ Process terminated"
else
  echo "No process found on port $PORT"
fi

# Alternative using fuser (if lsof not available)
fuser -k 3000/tcp
```

#### Windows PowerShell:
```powershell
# Method 1: Using Get-NetTCPConnection (Windows 10+)
$port = 3000
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
if ($process) {
    Stop-Process -Id $process -Force
    Write-Host "✓ Killed process on port $port (PID: $process)"
} else {
    Write-Host "No process found on port $port"
}

# Method 2: Using netstat (Universal Windows)
netstat -ano | findstr :3000 | ForEach-Object {
    $fields = $_ -split '\s+'
    $pid = $fields[-1]
    if ($pid -match '^\d+$') {
        taskkill /PID $pid /F
        Write-Host "✓ Killed process on port 3000 (PID: $pid)"
    }
}
```

---

### 2. PID-Specific Termination

**Use this when**: You have the exact Process ID (PID).

#### Linux/macOS:
```bash
# Kill specific PID
kill -9 12345

# With verification
PID=12345
if ps -p $PID > /dev/null; then
   kill -9 $PID
   echo "✓ Process $PID terminated"
else
   echo "Process $PID not found"
fi
```

#### Windows PowerShell:
```powershell
# Kill specific PID
Stop-Process -Id 12345 -Force

# With verification
$pid = 12345
if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
    Stop-Process -Id $pid -Force
    Write-Host "✓ Process $pid terminated"
} else {
    Write-Host "Process $pid not found"
}
```

---

### 3. npm/yarn Script Termination

**Use this when**: Process was started via package.json scripts.

#### All Platforms:
```bash
# Use built-in package manager stop commands
npm stop
yarn stop

# Or use custom package.json scripts
npm run stop-server
npm run kill-dev

# Example package.json:
{
  "scripts": {
    "start": "node server.js",
    "stop": "pkill -f 'node server.js'"  # Note: specific script name
  }
}
```

---

### 4. Process Name with Specific Script (Advanced)

**Use this when**: You need to kill a specific script by name, NOT all Node processes.

#### Linux/macOS:
```bash
# ✅ SAFE - Only kills processes matching EXACT script name
pkill -f "node server.js"      # Only "node server.js"
pkill -f "node dist/index.js"  # Only "node dist/index.js"
pkill -f "npm run dev"         # Only "npm run dev"

# ✅ SAFE - Kill by working directory
pkill -f "/path/to/project/server.js"

# Verification before kill
ps aux | grep "node server.js" | grep -v grep
```

#### Windows PowerShell:
```powershell
# ✅ SAFE - Filter by specific command line
Get-WmiObject Win32_Process | Where-Object {
    $_.CommandLine -like "*server.js*"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
    Write-Host "✓ Killed $($_.CommandLine)"
}

# Alternative using CIM (faster)
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like "*node server.js*"
} | Stop-Process -Force
```

**⚠️ WARNING**: Even "specific script" matching can be dangerous if the pattern is too broad. Always verify what you're killing first.

---

## 🛡️ VERIFICATION BEFORE TERMINATION

**Always verify what you're about to kill BEFORE executing kill command:**

### Linux/macOS Verification:
```bash
# Check what's on a specific port
lsof -ti :3000
ps -p $(lsof -ti :3000)  # Show process details

# List all node processes (review before killing)
ps aux | grep node | grep -v grep

# Show process tree
pstree -p $(lsof -ti :3000)
```

### Windows Verification:
```powershell
# Check what's on a specific port
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess

# List all node processes (review before killing)
Get-Process -Name node | Select-Object Id, ProcessName, Path, StartTime

# Show detailed process info
Get-WmiObject Win32_Process | Where-Object {$_.Name -eq "node.exe"} |
    Select-Object ProcessId, CommandLine
```

---

## 🚨 ESCALATION PATTERN TO AVOID

### ❌ WRONG Approach (Leads to Self-Termination):
```
1. User: "Stop the dev server on port 3000"
2. Agent: Tries `lsof -ti :3000 | xargs kill` → Fails (permission issue)
3. Agent: Escalates to `pkill -f node` → Fails (too cautious)
4. Agent: Escalates to `pkill node` → 💥 CLAUDE CODE TERMINATES
5. Result: VS Code crashes, user loses work, session destroyed
```

### ✅ CORRECT Approach (Safe Escalation):
```
1. User: "Stop the dev server on port 3000"
2. Agent: Tries `lsof -ti :3000 | xargs kill -9` → Success ✓
3. If fails: Verify port with `lsof -ti :3000` (check output)
4. If no process found: Inform user "No process on port 3000"
5. If permission denied: Ask user to run with sudo or elevated privileges
6. NEVER escalate to broad node process termination
```

---

## 📝 AGENT-SPECIFIC GUIDELINES

### Gojo (Mission Control)

**When to use**:
- Cleaning up processes during project shutdown
- Stopping services during tier transitions
- Emergency cleanup procedures

**Rules**:
- ✅ ALWAYS use port-specific termination (lsof -ti :PORT | xargs kill -9)
- ✅ Document which ports are managed in project-state.json
- ❌ NEVER use pkill node in cleanup procedures
- ❌ NEVER use killall node
- ✅ Verify process exists before termination attempt
- ✅ Log all process termination attempts in trigger-19.md

**Example Cleanup Procedure**:
```bash
# ✅ SAFE - Gojo cleanup
PORTS=(3000 3001 5432 6379)  # Frontend, API, Postgres, Redis
for PORT in "${PORTS[@]}"; do
  PID=$(lsof -ti :$PORT)
  if [ ! -z "$PID" ]; then
    kill -9 $PID
    echo "Stopped process on port $PORT"
  fi
done
```

---

### Panda (Build & Integration)

**When to use**:
- Managing dev server lifecycle (start/stop/restart)
- Build process cleanup
- CI/CD pipeline process management
- Integration test server management

**Rules**:
- ✅ Use npm stop / yarn stop for managed processes
- ✅ Use port-specific termination for dev servers
- ✅ Document ports used in dev-notes.md
- ✅ Prefer package.json scripts over direct kill commands
- ❌ NEVER use pkill node in build scripts
- ❌ NEVER use killall node in CI/CD pipelines

**Development Server Management**:
```bash
# ✅ SAFE - Panda dev server management

# Start dev server (document port)
npm run dev  # Runs on port 3000 (documented in dev-notes.md)

# Stop dev server (port-specific)
lsof -ti :3000 | xargs kill -9

# Restart dev server
lsof -ti :3000 | xargs kill -9 && npm run dev
```

**CI/CD Pipeline**:
```yaml
# ✅ SAFE - GitHub Actions example
- name: Start test server
  run: npm run test:server &

- name: Run tests
  run: npm test

- name: Cleanup test server
  run: lsof -ti :3001 | xargs kill -9  # Port-specific cleanup
  if: always()  # Run even if tests fail
```

---

### Yuuji (Implementation)

**When to use**:
- Running test servers during TDD
- Integration test setup/teardown
- Development workflow automation
- Local testing cleanup

**Rules**:
- ✅ Note port numbers in dev-notes.md when starting test servers
- ✅ Use port-specific cleanup in test teardown
- ✅ Document cleanup procedures for all test infrastructure
- ❌ NEVER use pkill node in test cleanup
- ❌ NEVER use killall node in test teardown
- ✅ Use try/finally blocks to ensure cleanup runs

**Test Server Pattern**:
```python
# ✅ SAFE - Yuuji test server management
import subprocess
import requests
import time

def test_api_endpoint():
    # Start test server on specific port
    server = subprocess.Popen(
        ["node", "test-server.js"],
        env={"PORT": "3002"}  # Specific port for testing
    )

    # Wait for server to be ready
    time.sleep(2)

    try:
        # Run tests
        response = requests.get("http://localhost:3002/health")
        assert response.status_code == 200
    finally:
        # ✅ SAFE - Kill by PID, not by name
        server.terminate()
        server.wait(timeout=5)

        # Backup cleanup (port-specific)
        subprocess.run(["bash", "-c", "lsof -ti :3002 | xargs kill -9"])
```

**Test Cleanup (pytest)**:
```python
# ✅ SAFE - pytest fixture with port-specific cleanup
import pytest
import subprocess

@pytest.fixture(scope="session")
def test_server():
    # Start server
    server = subprocess.Popen(["node", "server.js"], env={"PORT": "3003"})
    yield server

    # ✅ SAFE - Cleanup by PID
    server.terminate()
    server.wait()

    # Port-specific backup cleanup
    subprocess.run(["bash", "-c", "lsof -ti :3003 | xargs kill -9"])
```

---

### All Agents - Universal Rules

**Before Any Process Termination**:
1. ✅ **Verify target**: Check what process you're killing
2. ✅ **Use port-specific**: Prefer lsof/netstat + port number
3. ✅ **Use PID-specific**: If you have exact PID, use it
4. ✅ **Document ports**: Note all ports used in dev-notes.md
5. ❌ **NEVER use broad commands**: No pkill node, killall node

**When Termination Fails**:
1. ✅ **Check permissions**: May need sudo/admin rights
2. ✅ **Verify process exists**: Use ps/lsof/netstat to confirm
3. ✅ **Ask user**: Request clarification on which process to kill
4. ❌ **DO NOT escalate to broad kill**: Never try pkill node as fallback

**Emergency User Override**:
If user explicitly requests `pkill node`:
1. ⚠️ **WARN IMMEDIATELY**: "This will terminate Claude Code and VS Code"
2. ⚠️ **EXPLAIN IMPACT**: "You will lose unsaved work and this session"
3. ⚠️ **OFFER ALTERNATIVE**: "Use port-specific termination instead: lsof -ti :PORT | xargs kill"
4. ✅ **ONLY PROCEED**: If user confirms understanding and still wants to proceed

---

## 🔧 TROUBLESHOOTING

### "Port is in use but lsof shows nothing"

**Cause**: Process may be running as different user or port is actually free.

**Solution**:
```bash
# Check with elevated privileges
sudo lsof -ti :3000

# Check if port is actually listening
netstat -tuln | grep :3000

# Try netstat instead of lsof
netstat -tlnp | grep :3000
```

### "Process won't die even with kill -9"

**Cause**: Process may be in uninterruptible sleep state (D state) or zombie.

**Solution**:
```bash
# Check process state
ps aux | grep <PID>

# If zombie (Z state), kill parent process
ps -o ppid= -p <PID>  # Get parent PID
kill -9 <PARENT_PID>

# If uninterruptible (D state), wait or reboot (system issue)
```

### "Permission denied when killing process"

**Cause**: Process owned by different user or requires admin privileges.

**Solution**:
```bash
# Linux/macOS
sudo lsof -ti :3000 | xargs sudo kill -9

# Windows PowerShell (run as Administrator)
Start-Process powershell -Verb RunAs -ArgumentList "-Command",
    "Stop-Process -Id <PID> -Force"
```

---

## 📚 REFERENCES

**External Resources**:
- Claude Code Issue #3068: <https://github.com/anthropics/claude-code/issues/3068>
- lsof man page: <https://man7.org/linux/man-pages/man8/lsof.8.html>
- Process Management Best Practices: <https://www.kernel.org/doc/html/latest/process/index.html>

**Related Protocol Files**:
- `protocol/gojo.agent.md` - Mission Control cleanup procedures
- `protocol/panda.agent.md` - Build & Integration server management
- `protocol/yuuji.agent.md` - Test server lifecycle management

---

## 🛡️ SUMMARY: SAFE TERMINATION CHECKLIST

Before terminating any process, verify:
- [ ] Do I know the exact port number? → Use `lsof -ti :PORT | xargs kill -9`
- [ ] Do I know the exact PID? → Use `kill -9 <PID>`
- [ ] Was this started via npm/yarn? → Use `npm stop` or `yarn stop`
- [ ] Do I need to kill by script name? → Use `pkill -f "node specific-script.js"` (VERIFY FIRST)
- [ ] Have I verified what I'm killing? → Run `ps aux | grep <pattern>` first
- [ ] Am I ABSOLUTELY SURE this won't kill Claude Code? → Double-check before proceeding

**When in doubt, ASK THE USER. Better to confirm than to destroy the development environment.**

---

**END OF SAFE_PROCESS_TERMINATION.md**
