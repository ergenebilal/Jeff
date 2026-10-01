Write-Output "TEST_PS_OK"
[Console]::Out.Flush()
Start-Sleep -Milliseconds 900

$items = Get-ChildItem "C:\Users\lenovo\Desktop" -ErrorAction SilentlyContinue
Write-Output ("DESKTOP_ADET=" + @($items).Count)
foreach ($i in $items) { Write-Output ("ITEM=" + $i.Name) }
Write-Output ("ONEDRIVE_VAR=" + (Test-Path "C:\Users\lenovo\OneDrive\Desktop"))
$od = Get-ChildItem "C:\Users\lenovo\OneDrive\Desktop" -ErrorAction SilentlyContinue
Write-Output ("ONEDRIVE_ADET=" + @($od).Count)
foreach ($i in $od) { Write-Output ("OD_ITEM=" + $i.Name) }
[Console]::Out.Flush()
Start-Sleep -Milliseconds 900
