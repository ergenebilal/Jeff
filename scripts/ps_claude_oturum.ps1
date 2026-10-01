$base = "C:\Users\lenovo\.claude"
$proj = "$base\projects"
$rapor = New-Object System.Collections.ArrayList
if (Test-Path $base) {
  [void]$rapor.Add("CLAUDE_KLASORU_VAR=1")
  if (Test-Path $proj) {
    [void]$rapor.Add("PROJECTS_VAR=1")
    foreach ($d in (Get-ChildItem $proj -Directory -ErrorAction SilentlyContinue)) {
      [void]$rapor.Add("PROJE=" + $d.Name)
      $dosyalar = Get-ChildItem $d.FullName -Filter *.jsonl -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
      foreach ($f in $dosyalar) {
        [void]$rapor.Add("  DOSYA=" + $f.Name + " | " + $f.Length + " bayt | " + $f.LastWriteTime.ToString("dd.MM HH:mm"))
      }
    }
  } else {
    [void]$rapor.Add("PROJECTS_YOK")
  }
  [void]$rapor.Add("--- alt klasorler ---")
  foreach ($d in (Get-ChildItem $base -Directory -ErrorAction SilentlyContinue)) {
    [void]$rapor.Add("ALT=" + $d.Name)
  }
} else {
  [void]$rapor.Add("CLAUDE_KLASORU_YOK")
}
$metin = $rapor -join [Environment]::NewLine
$metin | ssh -o StrictHostKeyChecking=no -o BatchMode=yes hermes "cat > /tmp/winmd/claude.txt"

if (Test-Path $proj) {
  $en = Get-ChildItem $proj -Recurse -Filter *.jsonl -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($en) {
    $son = Get-Content $en.FullName -Tail 120 -Encoding UTF8
    $metin2 = $son -join [Environment]::NewLine
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($metin2))
    $b64 | ssh -o StrictHostKeyChecking=no -o BatchMode=yes hermes "cat > /tmp/winmd/oturum_son.b64"
  }
}
