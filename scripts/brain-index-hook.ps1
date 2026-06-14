$TimeoutSeconds = 30
if (-not $env:PYTHONIOENCODING) {
  $env:PYTHONIOENCODING = "utf-8"
}

function Write-CortexHookLog {
  param([string]$Message)
  try {
    if ($script:CortexDataDir) {
      $LogRoot = $script:CortexDataDir
    } else {
      $LogRoot = Join-Path $env:LOCALAPPDATA "dzp-cortex"
    }
    New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
    Add-Content -Path (Join-Path $LogRoot "index.log") -Value "$(Get-Date -Format o) $Message"
  } catch { }
}

try {
  $Repo = (git rev-parse --show-toplevel).Trim()
  $Brain = Join-Path $Repo ".protocol-state/brain/brain.py"
  $script:CortexDataDir = (python -c "import sys; from pathlib import Path; repo=Path(r'$Repo').resolve(); sys.path.insert(0, str(repo/'.protocol-state'/'brain')); from cortex import config, paths; cfg=config.load(repo); print(paths.data_dir(repo, cfg))").Trim()
  New-Item -ItemType Directory -Force -Path $script:CortexDataDir | Out-Null
  $Lock = Join-Path $script:CortexDataDir "index.lock"
  if (Test-Path $Lock) {
    Write-CortexHookLog "index hook skipped; lock exists"
    exit 0
  }
  New-Item -ItemType File -Path $Lock -ErrorAction Stop | Out-Null
  $Process = Start-Process -FilePath "python" -ArgumentList @($Brain, "--repo", $Repo, "index", "--incremental") -WindowStyle Hidden -PassThru
  if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
    try { Stop-Process -Id $Process.Id -Force } catch { }
    Write-CortexHookLog "index hook timed out after ${TimeoutSeconds}s"
  } elseif ($Process.ExitCode -ne 0) {
    Write-CortexHookLog "index hook exited with code $($Process.ExitCode)"
  }
} catch {
  Write-CortexHookLog "index hook failed: $_"
} finally {
  if ($Lock -and (Test-Path $Lock)) {
    try { Remove-Item -LiteralPath $Lock -Force } catch { }
  }
}

exit 0
