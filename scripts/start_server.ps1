# Start the webhook/media-stream server on port 8080
Set-Location $PSScriptRoot\..

Write-Host "Starting PGAI voice server on http://0.0.0.0:8080"
Write-Host "In another terminal run: ngrok http 8080"
Write-Host "Then set PUBLIC_WEBHOOK_URL in .env to your ngrok https URL and restart this server."
python -m uvicorn src.server:app --host 0.0.0.0 --port 8080
