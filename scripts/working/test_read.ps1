# Test READ - Query ordini

Write-Host "`nOttengo token XSUAA...`n" -ForegroundColor Cyan

$clientId = "sb-testJoule!t576522"
$clientSecret = "6f32a36a-3882-4cd0-9430-a87e099878cf`$i-k9re-OJROa1lbO9kkLdfQji4paoyB1_pvMlFwoUH8="
$tokenUrl = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com/oauth/token"
$serviceUrl = "https://otb-joule-s4-sb4-2e2gsnau-joule-s4-sb4-testjoule-srv.cfapps.eu10-004.hana.ondemand.com/odata/v4/mass-change"

# Ottieni token
$tokenBody = "grant_type=client_credentials&client_id=$clientId&client_secret=$clientSecret"
$token = Invoke-RestMethod -Uri $tokenUrl -Method POST -Headers @{"Content-Type"="application/x-www-form-urlencoded"} -Body $tokenBody

Write-Host "Token ottenuto`n" -ForegroundColor Green

# Chiama READ
Write-Host "Eseguo READ (Plant 142A)...`n" -ForegroundColor Yellow

$body = @{
    filters = @{
        materialStartsWith = "J01AA0119J3"
        plant = "142A"
        salesOrg = "142"
        creationDate = "2026-01-13"
    }
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "$serviceUrl/readOrders" -Method POST -Headers @{
    "Authorization" = "Bearer $($token.access_token)"
    "Content-Type" = "application/json"
} -Body $body

Write-Host "Risultato:" -ForegroundColor Green
$result | ConvertTo-Json -Depth 5
