# Verify a Power BI companion project in Power BI Desktop, without any mouse or keyboard input:
#   1. open the .pbip (a process start) and wait for its model to load in the local engine;
#   2. refresh the model with a TMSL refresh command sent to that engine;
#   3. run the project's Checks DAX query (one row per check: Section, Check, Expected, Actual, Agrees);
#   4. select each report page through UI Automation's SelectionItemPattern and read the names Desktop exposes for
#      what the canvas shows (visual titles, alt text, values, and any error message);
#   5. close only the Desktop instance this script started.
# Output: a JSON file with the checks and, per page, the names read.
param(
    [Parameter(Mandatory = $true)][string]$Pbip,
    [Parameter(Mandatory = $true)][string]$Table,
    [Parameter(Mandatory = $true)][string]$ChecksFile,
    [Parameter(Mandatory = $true)][string]$OutJson,
    [string]$Pages = "",                     # page display names separated by ";"
    [int]$RenderSeconds = 12,
    [switch]$DaxView,                         # also open DAX query view and read its query tabs
    [string]$RoleChecks = ""                  # optional JSON file: [{label, role, user, file}], each query run under Roles=
)
$ErrorActionPreference = "Stop"
$loc = (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation
Add-Type -Path "$loc\bin\Microsoft.PowerBI.AdomdClient.dll"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [System.Windows.Automation.AutomationElement]
$beforeDesk = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue | ForEach-Object Id)
$beforeSrv = @(Get-Process msmdsrv -ErrorAction SilentlyContinue | ForEach-Object Id)
$result = [ordered]@{ pbip = $Pbip; loaded = $false; refreshSeconds = $null; checks = @(); pages = [ordered]@{}; daxView = $null; error = $null }
Start-Process -FilePath $Pbip

function Open-Model {
    foreach ($p in Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'") {
        if ($beforeSrv -contains $p.ProcessId) { continue }
        $dir = [regex]::Match($p.CommandLine, '-s\s+"([^"]+)"').Groups[1].Value
        $portFile = Join-Path $dir "msmdsrv.port.txt"
        if (-not (Test-Path $portFile)) { continue }
        $port = [System.IO.File]::ReadAllText($portFile, [System.Text.Encoding]::Unicode).Trim()
        $c = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
        try {
            $c.Open(); $cmd = $c.CreateCommand(); $cmd.CommandText = "SELECT [Name] FROM `$SYSTEM.TMSCHEMA_TABLES"
            $r = $cmd.ExecuteReader(); $n = @(); while ($r.Read()) { $n += $r.GetValue(0) }; $r.Close()
            if ($n -contains $Table) { return @{ Conn = $c; Srv = $p.ProcessId } }
            $c.Close()
        } catch { try { $c.Close() } catch { } }
    }
    return $null
}

function Desktop-Windows($ids) {
    $root = $A::RootElement
    foreach ($id in $ids) {
        $cond = New-Object System.Windows.Automation.PropertyCondition($A::ProcessIdProperty, $id)
        foreach ($w in $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)) { $w }
    }
}

function Select-ByName($ids, [string]$name) {
    # a page tab (TabItem) wins over a page navigator's button of the same name on the canvas
    $fallback = $null
    foreach ($w in Desktop-Windows $ids) {
        $nc = New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $name)
        foreach ($e in $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $nc)) {
            $pat = $null
            if ($e.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$pat)) {
                if ($e.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem) { $pat.Select(); return $true }
                if (-not $fallback) { $fallback = $pat }
            }
        }
    }
    if ($fallback) { $fallback.Select(); return $true }
    return $false
}

function Read-Names($ids) {
    $names = New-Object System.Collections.Generic.List[string]
    foreach ($w in Desktop-Windows $ids) {
        foreach ($e in $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)) {
            try { $nm = $e.Current.Name; if ($nm) { $names.Add($nm.Trim()) } } catch { }
        }
    }
    return @($names | Select-Object -Unique)
}

$m = $null
$deadline = (Get-Date).AddMinutes(8)
while (-not $m -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 3; $m = Open-Model }
$newDesk = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue | Where-Object { $beforeDesk -notcontains $_.Id } | ForEach-Object Id)
try {
    if (-not $m) { throw "the model did not load within 8 minutes" }
    $result.loaded = $true
    $conn = $m.Conn
    $cmd = $conn.CreateCommand(); $cmd.CommandText = "SELECT [CATALOG_NAME] FROM `$SYSTEM.DBSCHEMA_CATALOGS"
    $r = $cmd.ExecuteReader(); $null = $r.Read(); $db = $r.GetValue(0); $r.Close()
    $t = Get-Date
    # Desktop may still be finishing its own load when the model appears, and a refresh sent then can return at once
    # and leave tables without data: refresh until every partition and relationship is ready, at most three times.
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $cmd = $conn.CreateCommand(); $cmd.CommandTimeout = 3600
        $cmd.CommandText = '{"refresh": {"type": "full", "objects": [{"database": "' + $db + '"}]}}'
        $null = $cmd.ExecuteNonQuery()
        $notReady = @()
        foreach ($q in @("SELECT [Name], [State], [ErrorMessage] FROM `$SYSTEM.TMSCHEMA_PARTITIONS",
                         "SELECT [ID], [State], [ID] FROM `$SYSTEM.TMSCHEMA_RELATIONSHIPS")) {
            $cmd = $conn.CreateCommand(); $cmd.CommandText = $q
            $r = $cmd.ExecuteReader()
            while ($r.Read()) { if ($r.GetValue(1) -ne 1) { $notReady += "$($r.GetValue(0)) (state $($r.GetValue(1))) $($r.GetValue(2))" } }
            $r.Close()
        }
        $result.refreshAttempts = $attempt
        if (-not $notReady) { break }
        Start-Sleep -Seconds 10
    }
    $result.refreshSeconds = [math]::Round(((Get-Date) - $t).TotalSeconds)
    if ($notReady) { throw "not refreshed after three attempts: " + ($notReady -join "; ") }
    $cmd = $conn.CreateCommand(); $cmd.CommandTimeout = 600
    $cmd.CommandText = [System.IO.File]::ReadAllText($ChecksFile)
    $r = $cmd.ExecuteReader()
    $rows = @()
    while ($r.Read()) {
        $row = [ordered]@{}
        for ($i = 0; $i -lt $r.FieldCount; $i++) {
            $key = ($r.GetName($i) -replace '^\[|\]$', '')
            $v = $r.GetValue($i)
            if ($v -is [System.DBNull]) { $v = $null }
            $row[$key] = $v
        }
        $rows += [pscustomobject]$row
    }
    $r.Close(); $conn.Close()
    $result.checks = $rows
    if ($RoleChecks) {
        # the same kind of checks query, run on a connection that applies a role (and, if given, an effective user)
        $result.roleChecks = [ordered]@{}
        foreach ($rc in (Get-Content -Raw -Path $RoleChecks | ConvertFrom-Json)) {
            $cs = $conn.ConnectionString + ";Roles=" + $rc.role
            if ($rc.user) { $cs += ";EffectiveUserName=" + $rc.user }
            $rconn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($cs)
            try {
                $rconn.Open(); $cmd = $rconn.CreateCommand(); $cmd.CommandTimeout = 600
                $cmd.CommandText = [System.IO.File]::ReadAllText($rc.file)
                $r = $cmd.ExecuteReader(); $rrows = @()
                while ($r.Read()) {
                    $row = [ordered]@{}
                    for ($i = 0; $i -lt $r.FieldCount; $i++) {
                        $v = $r.GetValue($i); if ($v -is [System.DBNull]) { $v = $null }
                        $row[($r.GetName($i) -replace '^\[|\]$', '')] = $v
                    }
                    $rrows += [pscustomobject]$row
                }
                $r.Close()
                $result.roleChecks[$rc.label] = [ordered]@{ rows = $rrows; error = $null }
            } catch {
                $result.roleChecks[$rc.label] = [ordered]@{ rows = @(); error = $_.Exception.Message }
            } finally { try { $rconn.Close() } catch { } }
        }
    }
    $pageList = @($Pages -split ";" | Where-Object { $_ })
    if ($pageList.Count) {
        $null = Select-ByName $newDesk "Report view"
        foreach ($p in $pageList) {
            # the page tabs appear a few seconds after Report view is selected
            $selected = $false; $until = (Get-Date).AddSeconds(30)
            while (-not $selected -and (Get-Date) -lt $until) {
                $selected = Select-ByName $newDesk $p
                if (-not $selected) { Start-Sleep -Seconds 2 }
            }
            Start-Sleep -Seconds $RenderSeconds
            $result.pages[$p] = [ordered]@{ selected = $selected; names = (Read-Names $newDesk) }
        }
    }
    if ($DaxView) {
        $selected = Select-ByName $newDesk "DAX query view"
        Start-Sleep -Seconds $RenderSeconds
        $result.daxView = [ordered]@{ selected = $selected; names = (Read-Names $newDesk) }
    }
} catch {
    $result.error = $_.Exception.Message
} finally {
    foreach ($id in $newDesk) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
    if ($m) { Stop-Process -Id $m.Srv -Force -ErrorAction SilentlyContinue }
    $result | ConvertTo-Json -Depth 6 | Set-Content -Path $OutJson -Encoding utf8
}
