$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskPlanPath = Join-Path $PSScriptRoot 'Ablageplan.json'
$taskPlan = Get-Content -LiteralPath $taskPlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([IO.Path]::GetFullPath($taskPlan.projektwurzel) -ne $taskRoot) {
    throw 'Ablageplan gehört zu einem anderen Projekt.'
}
$taskArchive = [IO.Path]::GetFullPath((Join-Path $taskRoot 'PDF_Archiv/02_In_Markdown_umgewandelt/Stand_2026-09-09'))
$taskMoves = @()
foreach ($taskDocument in $taskPlan.dokumente) {
    $taskSource = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskDocument.quelle))
    $taskTarget = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskDocument.eintrag.pdf))
    if (-not $taskSource.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Quelle außerhalb des Projekts: $taskSource"
    }
    if (-not $taskTarget.StartsWith($taskArchive + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Ziel außerhalb des vorgesehenen Archivs: $taskTarget"
    }
    if (Test-Path -LiteralPath $taskTarget) { throw "Ziel existiert bereits: $taskTarget" }
    $taskHash = (Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($taskHash -ne $taskDocument.eintrag.sha256_pdf) { throw "Quelle verändert: $taskSource" }
    $taskMoves += [PSCustomObject]@{ Source = $taskSource; Target = $taskTarget; Hash = $taskHash }
}
foreach ($taskMove in $taskMoves) {
    $taskParent = Split-Path -Path $taskMove.Target -Parent
    [IO.Directory]::CreateDirectory($taskParent) | Out-Null
    Move-Item -LiteralPath $taskMove.Source -Destination $taskMove.Target
    if ((Get-FileHash -LiteralPath $taskMove.Target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskMove.Hash) {
        throw "Archivprüfung fehlgeschlagen: $($taskMove.Target)"
    }
}
Write-Output "$($taskMoves.Count) Original-PDFs unverändert in ihre geprüften Archivordner verschoben."
