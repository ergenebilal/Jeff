# Plan dosyasini guvenilir sekilde sunucuya gonderir.
# ONEMLI: once yerel dosyaya yaz, sonra scp ile gonder.
# (Dogrudan boru hattina yazmak base64'u zaman zaman bozuyordu — 30.09.2026)
$f = "C:\Users\lenovo\Desktop\JEFF_TO_JARVIS_PLANI.md"
if (Test-Path $f) {
  $tmp = Join-Path $env:TEMP "plan_gonder.b64"
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f))
  [IO.File]::WriteAllText($tmp, $b64)
  scp -o StrictHostKeyChecking=no -o BatchMode=yes -q $tmp hermes:/tmp/winmd/plan.b64
}
