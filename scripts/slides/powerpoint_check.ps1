param(
    [string]$Deck = 'slides/_build/pptx/chapter-01/chapter-01.pptx',
    [string]$OutputDirectory = 'outputs/build/powerpoint-review'
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$deckPath = (Resolve-Path -LiteralPath (Join-Path $repoRoot $Deck)).Path
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
$buildRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'outputs/build'))
if (-not $outputPath.StartsWith($buildRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'PowerPoint review output must be a named directory under outputs/build.'
}
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
# Remove only screenshots owned by this checker, including obsolete slide numbers.
Get-ChildItem -LiteralPath $outputPath -File | Where-Object { $_.Name -match '^slide-\d+\.png$' } | ForEach-Object { Remove-Item -LiteralPath $_.FullName }
$app = New-Object -ComObject PowerPoint.Application
$presentation = $null
$copy = $null
try {
    # Open a dedicated hidden copy; never save over the generated deck.
    $presentation = $app.Presentations.Open($deckPath, 0, -1, 0)
    $slides = @()
    $issues = @()
    $tableEdited = $false
    $textEdited = $false
    foreach ($slide in $presentation.Slides) {
        $imagePath = Join-Path $outputPath ('slide-{0:D2}.png' -f $slide.SlideIndex)
        $slide.Export($imagePath, 'PNG', 1600, 900)
        $texts = @()
        $tables = @()
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                $range = $shape.TextFrame2.TextRange
                $texts += @{text=$range.Text; font_name=$range.Font.Name; font_size=$range.Font.Size; x=$shape.Left; y=$shape.Top; width=$shape.Width; height=$shape.Height; text_height=$range.BoundHeight}
                if ($range.BoundHeight -gt ($shape.Height + 3)) {
                    $issues += @{slide=$slide.SlideIndex; type='text-overflow'; text=$range.Text; height=$shape.Height; text_height=$range.BoundHeight}
                }
                if (-not $textEdited) {
                    $originalText = $shape.TextFrame.TextRange.Text
                    $shape.TextFrame.TextRange.Text = $originalText + ' [editability check]'
                    $textEdited = $shape.TextFrame.TextRange.Text.Contains('[editability check]')
                    $shape.TextFrame.TextRange.Text = $originalText
                }
            }
            if ($shape.HasTable) {
                $cells = @()
                for ($row = 1; $row -le $shape.Table.Rows.Count; $row++) {
                    for ($column = 1; $column -le $shape.Table.Columns.Count; $column++) {
                        $cellShape = $shape.Table.Cell($row,$column).Shape
                        $cellRange = $cellShape.TextFrame2.TextRange
                        $cells += @{row=$row; column=$column; text=$cellRange.Text; font_name=$cellRange.Font.Name; font_size=$cellRange.Font.Size; height=$cellShape.Height; text_height=$cellRange.BoundHeight}
                        if ($cellRange.BoundHeight -gt ($cellShape.Height + 3)) {
                            $issues += @{slide=$slide.SlideIndex; type='table-cell-overflow'; text=$cellRange.Text}
                        }
                    }
                }
                $tables += @{cells=$cells}
                if (-not $tableEdited) {
                    $cell = $shape.Table.Cell(1,1).Shape.TextFrame.TextRange
                    $originalCell = $cell.Text
                    $cell.Text = $originalCell + ' [editability check]'
                    $tableEdited = $cell.Text.Contains('[editability check]')
                    $cell.Text = $originalCell
                }
            }
        }
        $notes = @()
        foreach ($noteShape in $slide.NotesPage.Shapes) {
            if ($noteShape.HasTextFrame -and $noteShape.TextFrame.HasText) {
                $notes += $noteShape.TextFrame.TextRange.Text
            }
        }
        $slides += @{number=$slide.SlideIndex; texts=$texts; tables=$tables; notes=$notes; image=$imagePath}
    }
    $copyPath = Join-Path $outputPath 'editability-check.pptx'
    $presentation.SaveAs($copyPath, 24)
    $presentation.Close()
    $presentation = $null
    $copy = $app.Presentations.Open($copyPath, -1, 0, 0)
    $reopened = $copy.Slides.Count -eq $slides.Count
    $copy.Close()
    $copy = $null
    $report = @{engine='Microsoft PowerPoint'; version=$app.Version; artifact_sha256=(Get-FileHash -LiteralPath $deckPath -Algorithm SHA256).Hash.ToLower(); slide_count=$slides.Count; editable_text=$textEdited; editable_table=$tableEdited; saved_copy_reopened=$reopened; issues=$issues; slides=$slides; slideshow_ui='not-run'; screen_reader='not-run'; reading_order='not-run'}
    $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outputPath 'report.json') -Encoding UTF8
    Write-Output ('PowerPoint exported {0} slides; editable text={1}, table={2}; overflow flags={3}' -f $slides.Count,$textEdited,$tableEdited,$issues.Count)
} finally {
    if ($null -ne $copy) { $copy.Close() }
    if ($null -ne $presentation) { $presentation.Close() }
    # PowerPoint may share an application instance with the author; do not Quit it.
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
