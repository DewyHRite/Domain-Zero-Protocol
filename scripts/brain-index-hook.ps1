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
  # B6: pass $Repo as a DATA argument (sys.argv[1]) rather than interpolating
  # it into the Python source string.  Interpolation breaks on paths that
  # contain single-quotes and can alter the snippet being executed.
  $script:CortexDataDir = (python -c "import sys; from pathlib import Path; repo=Path(sys.argv[1]).resolve(); sys.path.insert(0, str(repo/'.protocol-state'/'brain')); from cortex import config, paths; cfg=config.load(repo); print(paths.data_dir(repo, cfg))" $Repo).Trim()
  New-Item -ItemType Directory -Force -Path $script:CortexDataDir | Out-Null
  $Lock = Join-Path $script:CortexDataDir "index.lock"
  # B7: atomic lock acquisition — rely solely on New-Item -ErrorAction Stop.
  # Removing the prior Test-Path guard eliminates the TOCTOU window where two
  # concurrent invocations could both pass the existence check before either
  # creates the file.  New-Item on an existing path throws with -ErrorAction Stop,
  # so the catch block handles the "lock held" case without a separate check.
  # $script:LockAcquired tracks ownership so the finally block only removes a
  # lock that THIS invocation created (ownership-safe cleanup).
  $script:LockAcquired = $false
  try {
    New-Item -ItemType File -Path $Lock -ErrorAction Stop | Out-Null
    $script:LockAcquired = $true
  } catch {
    Write-CortexHookLog "index hook skipped; lock exists (concurrent run)"
    exit 0
  }
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
  # B7: ownership-safe cleanup — only remove the lock if this invocation acquired it.
  if ($script:LockAcquired -and $Lock -and (Test-Path $Lock)) {
    try { Remove-Item -LiteralPath $Lock -Force } catch { }
  }
}

exit 0
