# Place one test call (after server + ngrok are running and .env is filled)
param(
    [string]$Scenario = "schedule_simple"
)

Set-Location $PSScriptRoot\..

python -m src.call_runner --scenario $Scenario
