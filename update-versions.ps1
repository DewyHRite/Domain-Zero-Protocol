# Update all v8.6.0 references to v8.7.0 in current project files (excluding backups and core-files-v8.5.1)

Write-Host "Updating version references from v8.6.0 to v8.7.0..."

# Get all markdown, yaml, json files in current project (exclude backups and core-files)
$files = Get-ChildItem -Path . -Recurse -File -Include *.md,*.yaml,*.json |
    Where-Object { $_.FullName -notmatch '\\backup' -and $_.FullName -notmatch '\\core-files-v8\.5\.1' }

$updated = 0
foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -ne $content -and $content -match '8\.6\.0') {
        $newContent = $content -replace '8\.6\.0', '8.7.0' -replace 'v8\.6\.0', 'v8.7.0'
        Set-Content -Path $file.FullName -Value $newContent -NoNewline
        Write-Host "Updated: $($file.Name)"
        $updated++
    }
}

Write-Host "`nTotal files updated: $updated"
