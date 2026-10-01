$dirs = @("C:\Users\lenovo\Desktop", "C:\Users\lenovo\OneDrive\Desktop")
$rapor = New-Object System.Collections.ArrayList
foreach ($d in $dirs) {
  if (Test-Path $d) {
    [void]$rapor.Add("DIR=" + $d)
    foreach ($i in (Get-ChildItem $d -ErrorAction SilentlyContinue)) {
      [void]$rapor.Add("  " + $i.Name + "  [" + $i.Length + "]")
    }
  } else {
    [void]$rapor.Add("DIR_YOK=" + $d)
  }
}
$metin = $rapor -join [Environment]::NewLine
$metin | ssh -o StrictHostKeyChecking=no -o BatchMode=yes hermes "cat > /tmp/winmd/liste.txt"

foreach ($d in $dirs) {
  if (Test-Path $d) {
    foreach ($f in (Get-ChildItem $d -Filter "*.md" -ErrorAction SilentlyContinue)) {
      $safe = ($f.Name -replace '[^A-Za-z0-9._-]', '_')
      $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.FullName))
      $b64 | ssh -o StrictHostKeyChecking=no -o BatchMode=yes hermes "cat > /tmp/winmd/$safe.b64"
    }
  }
}
