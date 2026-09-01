param(
  [Parameter(Mandatory=$true)][string]$ApiUrl,
  [Parameter(Mandatory=$true)][string]$ApiKey,
  [string]$SourceName = "BLUEORCH-WIN-01",
  [ValidateSet("security","system","full")][string]$Profile = "security"
)
$ErrorActionPreference = "Stop"
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw "Run PowerShell as Administrator" }
$Python = (Get-Command python -ErrorAction Stop).Source
$InstallDir = Join-Path $env:ProgramData "BlueOrch\Agent"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot "blueorch_agent.py") (Join-Path $InstallDir "blueorch_agent.py") -Force
$Config = @{ api_url=$ApiUrl.TrimEnd('/'); api_key=$ApiKey; source_name=$SourceName; profile=$Profile; poll_seconds=15; state_file=(Join-Path $InstallDir "state.json"); spool_file=(Join-Path $InstallDir "spool.json") }
$Config | ConvertTo-Json | Set-Content (Join-Path $InstallDir "config.json") -Encoding UTF8
$Action = New-ScheduledTaskAction -Execute $Python -Argument ('"{0}" --config "{1}"' -f (Join-Path $InstallDir "blueorch_agent.py"),(Join-Path $InstallDir "config.json"))
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "BlueOrch Log Agent" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
Start-ScheduledTask -TaskName "BlueOrch Log Agent"
Write-Host "BlueOrch agent installed and started: $InstallDir" -ForegroundColor Cyan
