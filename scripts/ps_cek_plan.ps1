$ErrorActionPreference = "Stop"
$f = "C:\Users\lenovo\Desktop\Jeff\JEFF_TO_JARVIS_PLANI.md"
if (-not (Test-Path $f)) { Write-Output "DOSYA_YOK"; exit 1 }
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f))
$b64 | ssh -o StrictHostKeyChecking=no -o BatchMode=yes hermes "cat > /tmp/winmd/plan_yeni.b64"
if ($LASTEXITCODE -eq 0) { Write-Output ("GONDERILDI uzunluk=" + $b64.Length) } else { Write-Output ("HATA cikis=" + $LASTEXITCODE) }
