# Run DAX queries against the open Power BI Desktop model that holds a given table.
# Usage: powershell -File dax_check.ps1 -QueryFile queries.dax [-Table GLEntry]
# Queries in the file are separated by lines that start with "-- @@ " followed by a label.
param(
    [Parameter(Mandatory = $true)][string]$QueryFile,
    [string]$Table = "SalesInvoiceLine",
    [string]$Roles = ""
)
$ErrorActionPreference = "Stop"
$loc = (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation
Add-Type -Path "$loc\bin\Microsoft.PowerBI.AdomdClient.dll"

function Find-Port {
    foreach ($p in Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'") {
        $dir = [regex]::Match($p.CommandLine, '-s\s+"([^"]+)"').Groups[1].Value
        $portFile = Join-Path $dir "msmdsrv.port.txt"
        if (-not (Test-Path $portFile)) { continue }
        $port = [System.IO.File]::ReadAllText($portFile, [System.Text.Encoding]::Unicode).Trim()
        $c = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
        try {
            $c.Open()
            $cmd = $c.CreateCommand()
            $cmd.CommandText = "SELECT [Name] FROM `$SYSTEM.TMSCHEMA_TABLES"
            $r = $cmd.ExecuteReader()
            $names = @()
            while ($r.Read()) { $names += $r.GetValue(0) }
            $r.Close()
            if ($names -contains $Table) { return $port }
        } catch { } finally { $c.Close() }
    }
    throw "No open model contains table $Table"
}

$port = Find-Port
Write-Output "port $port"
$text = [System.IO.File]::ReadAllText($QueryFile)
$blocks = [regex]::Split($text, "(?m)^-- @@ ")
$cs = "Data Source=localhost:$port"
if ($Roles) { $cs += ";Roles=$Roles"; Write-Output "roles $Roles" }
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($cs)
$conn.Open()
foreach ($b in $blocks) {
    if (-not $b.Trim()) { continue }
    $nl = $b.IndexOf("`n")
    $label = $b.Substring(0, $nl).Trim()
    $query = $b.Substring($nl + 1)
    Write-Output "== $label"
    try {
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = $query
        $r = $cmd.ExecuteReader()
        $cols = @(); for ($i = 0; $i -lt $r.FieldCount; $i++) { $cols += $r.GetName($i) }
        Write-Output ("   " + ($cols -join " | "))
        $n = 0
        while ($r.Read() -and $n -lt 60) {
            $vals = @(); for ($i = 0; $i -lt $r.FieldCount; $i++) { $v = $r.GetValue($i); if ($v -is [double] -or $v -is [decimal]) { $vals += ([double]$v).ToString("0.######") } else { $vals += "$v" } }
            Write-Output ("   " + ($vals -join " | ")); $n++
        }
        $r.Close()
    } catch { Write-Output "   ERROR: $($_.Exception.Message)" }
}
$conn.Close()
