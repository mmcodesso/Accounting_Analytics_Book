param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [string]$OutputDirectory = 'outputs/build/word-check'
)
# Opens a copy of a DOCX in a new, hidden Word instance (never one you are working in), counts its pages and
# pictures, and saves it as a PDF next to the copy so the pages can be looked at (scripts/ebook_preview.py).
# Nothing is saved over the original.
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$docPath = (Resolve-Path -LiteralPath $Docx).Path
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
$buildRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'outputs/build'))
if (-not $outputPath.StartsWith($buildRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The Word check output must be a named directory under outputs/build.'
}
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
$copy = Join-Path $outputPath 'document.docx'
$pdf = Join-Path $outputPath 'document.pdf'
$result = Join-Path $outputPath 'result.json'
foreach ($old in @($copy, $pdf, $result)) { if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Force } }
Copy-Item -LiteralPath $docPath -Destination $copy

$before = @(Get-Process -Name WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$mine = @(Get-Process -Name WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Where-Object { $before -notcontains $_ })
$document = $null
try {
    # FileName, ConfirmConversions, ReadOnly, AddToRecentFiles
    $document = $word.Documents.Open($copy, $false, $true, $false)
    $pages = $document.ComputeStatistics(2)
    $inline = $document.InlineShapes.Count
    $document.ExportAsFixedFormat($pdf, 17)
    # The result is written before the document is closed: Word can drop the connection while it closes a
    # book of this size (RPC_E_DISCONNECTED), after everything above has been done.
    @{ opened = $true; pages = $pages; inline_shapes = $inline; pdf = $pdf; word_version = $word.Version } |
        ConvertTo-Json | Set-Content -LiteralPath $result -Encoding UTF8
}
finally {
    foreach ($step in @({ if ($document) { $document.Close(0) } }, { $word.Quit() })) {
        try { & $step } catch { Write-Warning "Word did not close cleanly: $($_.Exception.Message)" }
    }
    # Wait for this instance to leave; end it if it hangs, and never another Word process.
    foreach ($id in $mine) {
        $process = Get-Process -Id $id -ErrorAction SilentlyContinue
        if ($process -and -not $process.WaitForExit(20000)) { Stop-Process -Id $id -Force }
    }
}
Get-Content -LiteralPath $result
