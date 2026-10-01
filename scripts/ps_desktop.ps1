$paths = @("$env:USERPROFILE\Desktop", "$env:USERPROFILE\OneDrive\Desktop", "C:\Users\lenovo\Desktop")
foreach ($p in $paths) {
  if (Test-Path $p) {
    Write-Output "=== $p ==="
    $md = Get-ChildItem $p -Filter *.md -ErrorAction SilentlyContinue
    if ($md) {
      $md | Select-Object Name, Length, @{N='Degisti';E={$_.LastWriteTime.ToString('dd.MM HH:mm')}} | Format-Table -AutoSize | Out-String -Width 250
    } else {
      Write-Output "  (.md dosyasi yok)"
    }
  }
}
Write-Output "=== MASAUSTUNDEKI TUM DOSYALAR ==="
foreach ($p in $paths) {
  if (Test-Path $p) {
    Get-ChildItem $p -File -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize | Out-String -Width 250
    break
  }
}
