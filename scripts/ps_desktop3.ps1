Write-Output "TEST_PS_OK"
Write-Output ("DESKTOP_VAR=" + (Test-Path "C:\Users\lenovo\Desktop"))
$items = Get-ChildItem "C:\Users\lenovo\Desktop" -ErrorAction SilentlyContinue
Write-Output ("ADET=" + @($items).Count)
foreach ($i in $items) { Write-Output ("ITEM=" + $i.Name) }
Write-Output ("ONEDRIVE_VAR=" + (Test-Path "C:\Users\lenovo\OneDrive\Desktop"))
$od = Get-ChildItem "C:\Users\lenovo\OneDrive\Desktop" -ErrorAction SilentlyContinue
Write-Output ("ONEDRIVE_ADET=" + @($od).Count)
foreach ($i in $od) { Write-Output ("OD_ITEM=" + $i.Name) }
