$ErrorActionPreference = "SilentlyContinue"
Stop-ScheduledTask -TaskName "BlueOrch Log Agent"
Unregister-ScheduledTask -TaskName "BlueOrch Log Agent" -Confirm:$false
Write-Host "BlueOrch agent task removed. Configuration remains in ProgramData for recovery." -ForegroundColor Cyan
