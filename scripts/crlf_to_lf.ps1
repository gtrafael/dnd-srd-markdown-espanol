param(
    [string]$Path = (Join-Path $PSScriptRoot ".."),
    [switch]$WhatIf
)

$mdFiles = Get-ChildItem -Path $Path -Filter "*.md" -Recurse -File

$total = $mdFiles.Count
$converted = 0

foreach ($file in $mdFiles) {
    $content = [System.IO.File]::ReadAllText($file.FullName)
    if ($content.Contains("`r`n")) {
        $newContent = $content.Replace("`r`n", "`n")
        if (-not $WhatIf) {
            [System.IO.File]::WriteAllText($file.FullName, $newContent)
        }
        $converted++
        Write-Host "CRLF -> LF: $($file.FullName)"
    }
}

Write-Host ""
Write-Host "Done. $converted of $total markdown files converted from CRLF to LF."
if ($WhatIf) { Write-Host "(WhatIf mode - no files were modified)" }
