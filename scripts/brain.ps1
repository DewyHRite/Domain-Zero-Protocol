$ErrorActionPreference = "Stop"
$Repo = (git rev-parse --show-toplevel).Trim()
if (-not $env:PYTHONIOENCODING) {
    $env:PYTHONIOENCODING = "utf-8"
}
python (Join-Path $Repo ".protocol-state/brain/brain.py") --repo $Repo @args
