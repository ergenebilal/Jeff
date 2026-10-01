Write-Output ("USERPROFILE=" + $env:USERPROFILE)
Write-Output ("USERNAME=" + $env:USERNAME)
$d = "$env:USERPROFILE\Desktop"
Write-Output ("desktop_var_mi=" + (Test-Path $d))
Write-Output ("alt_desktop_var_mi=" + (Test-Path "C:\Users\lenovo\Desktop"))
Write-Output ("onedrive_desktop_var_mi=" + (Test-Path "C:\Users\lenovo\OneDrive\Desktop"))
Write-Output "--- Desktop icerigi ---"
Get-ChildItem "C:\Users\lenovo\Desktop" -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Output ("ITEM: " + $_.Name)
}
Write-Output "--- OneDrive Desktop icerigi ---"
Get-ChildItem "C:\Users\lenovo\OneDrive\Desktop" -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Output ("ITEM: " + $_.Name)
}
