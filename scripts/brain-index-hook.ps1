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
  # Staleness threshold: a lock older than this is treated as orphaned.
  # 600 s is well above any real index run (timeout cap: 30 s).
  $StaleSeconds = 600
  $script:LockAcquired = $false
  try {
    New-Item -ItemType File -Path $Lock -ErrorAction Stop | Out-Null
    $script:LockAcquired = $true
  } catch {
    # Lock already exists — check if it is stale (orphaned from a killed hook).
    $IsStale = $false
    try {
      if (Test-Path -LiteralPath $Lock) {
        $LockAge = ((Get-Date) - (Get-Item -LiteralPath $Lock).LastWriteTime).TotalSeconds
        $IsStale = $LockAge -gt $StaleSeconds
      }
    } catch { }

    if ($IsStale) {
      Write-CortexHookLog "index hook: reaping stale lock (age > ${StaleSeconds}s); retrying acquire"
      try { Remove-Item -LiteralPath $Lock -Force -ErrorAction SilentlyContinue } catch { }
      # Retry acquire once after reaping the stale lock.
      try {
        New-Item -ItemType File -Path $Lock -ErrorAction Stop | Out-Null
        $script:LockAcquired = $true
      } catch {
        Write-CortexHookLog "index hook skipped; lock re-acquired by concurrent run after reap"
        exit 0
      }
    } else {
      Write-CortexHookLog "index hook skipped; lock exists (concurrent run)"
      exit 0
    }
  }
  # SEC-CORTEX-012 (v9.3.4): capture stderr to a temp file so non-zero exits
  # produce a meaningful log entry (mirrors what the .sh hook already does via
  # 2>>index.log).  The temp file is appended to the hook log then removed.
  $script:StderrTemp = [System.IO.Path]::GetTempFileName()
  $Process = Start-Process -FilePath "python" -ArgumentList @($Brain, "--repo", $Repo, "index", "--incremental") -WindowStyle Hidden -PassThru -RedirectStandardError $script:StderrTemp
  if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
    try { Stop-Process -Id $Process.Id -Force } catch { }
    Write-CortexHookLog "index hook timed out after ${TimeoutSeconds}s"
  } elseif ($Process.ExitCode -ne 0) {
    Write-CortexHookLog "index hook exited with code $($Process.ExitCode)"
    if (Test-Path $script:StderrTemp) {
      $StderrContent = Get-Content -LiteralPath $script:StderrTemp -Raw -ErrorAction SilentlyContinue
      if ($StderrContent) {
        Write-CortexHookLog "index hook stderr: $($StderrContent.Trim())"
      }
    }
  }
} catch {
  Write-CortexHookLog "index hook failed: $_"
} finally {
  # B7: ownership-safe cleanup — only remove the lock if this invocation acquired it.
  if ($script:LockAcquired -and $Lock -and (Test-Path $Lock)) {
    try { Remove-Item -LiteralPath $Lock -Force } catch { }
  }
  # SEC-CORTEX-012: ensure temp file is removed on all paths, including Start-Process throw.
  if ($script:StderrTemp -and (Test-Path $script:StderrTemp)) {
    try { Remove-Item -LiteralPath $script:StderrTemp -Force } catch { }
  }
}

exit 0
