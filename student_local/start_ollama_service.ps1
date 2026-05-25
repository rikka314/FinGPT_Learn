param(
    [string]$BindAddress = "0.0.0.0:11435",
    [string]$ModelsPath = "D:\ollama\models"
)

$ollamaExe = (Get-Command ollama -ErrorAction Stop).Source
$cmd = '/c set OLLAMA_HOST=' + $BindAddress + '&& set OLLAMA_MODELS=' + $ModelsPath + '&& "' + $ollamaExe + '" serve'
$clientAddress = $BindAddress.Replace("0.0.0.0", "127.0.0.1")
$wslGateway = Get-NetIPAddress -InterfaceAlias "vEthernet (WSL (Hyper-V firewall))" -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty IPAddress -First 1

Start-Process -FilePath "cmd.exe" -ArgumentList $cmd -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 3

$env:OLLAMA_HOST = $clientAddress
Write-Host "Started Ollama server at http://$BindAddress"
Write-Host "Models path: $ModelsPath"
Write-Host "Windows client endpoint: http://$clientAddress"
if ($wslGateway) {
    Write-Host "WSL client endpoint: http://${wslGateway}:$($BindAddress.Split(':')[-1])"
}
ollama list
