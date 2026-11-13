# List build agents that are offline or running an old version. Works on a Windows agent host.
param([string]$AgentRoot = "C:\agents", [string]$MinVersion = "3.240.0")
$ErrorActionPreference = "Stop"

Get-ChildItem $AgentRoot -Directory | ForEach-Object {
    $svc = Get-Service -Name "vstsagent*$($_.Name)*" -ErrorAction SilentlyContinue
    $ver = (Get-Content (Join-Path $_.FullName ".agent") -Raw | ConvertFrom-Json).agentVersion
    [pscustomobject]@{
        Agent   = $_.Name
        Running = [bool]($svc -and $svc.Status -eq "Running")
        Version = $ver
        Old     = [version]$ver -lt [version]$MinVersion
    }
} | Where-Object { -not $_.Running -or $_.Old } | Format-Table -AutoSize
