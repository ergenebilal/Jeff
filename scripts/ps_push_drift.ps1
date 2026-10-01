$hedef = 'C:\Users\lenovo\pablo_drift_check.ps1'
if (Test-Path $hedef) {
    Copy-Item $hedef "$hedef.bak-pre-gitfix-20261001" -Force
    Write-Output "yedek alindi"
}
$satirlar = ssh hermes "cat /home/hermes/scripts/pablo_drift_check.ps1"
[IO.File]::WriteAllText($hedef, (($satirlar -join "`r`n") + "`r`n"))
$boyut = (Get-Item $hedef).Length
Write-Output ("yazildi, uzunluk=" + $boyut)
Write-Output ("sha256=" + (Get-FileHash $hedef -Algorithm SHA256).Hash)
