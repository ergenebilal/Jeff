# Pablo'nun calistigi C:\CyberGene\HermesNode ile git deposundaki pablo/ klasoru
# arasinda kod farki var mi diye gunluk kontrol. Sadece raporlar/uyarir; hicbir
# dosyayi otomatik kopyalamaz veya commit etmez (--sync bilerek kullanilmiyor).
#
# 01.10.2026 DUZELTME (5.7): git fetch/pull cagrilari '$ErrorActionPreference=Stop'
# altinda calisirken, git ilerleme bilgisini stderr'e yazinca PowerShell bunu
# "NativeCommandError" sayip betigi olduruyordu (exit 1 -> YANLIS ALARM).
# Artik git cagrilari 'Continue' altinda calisir, cikis kodlari elle toplanir;
# yalnizca gercek drift (pablo_drift.py exit != 0) alarm uretir.
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\lenovo\Desktop\jeff-pablo-codex-spec\Jeff-source'
$log = 'C:\Users\lenovo\logs\pablo_drift.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'

Set-Location $repo

# --- git tazeleme: stderr gurultusu hata sayilmasin ---
$ErrorActionPreference = 'Continue'
& git fetch origin --quiet 2>&1 | Out-Null
$fetchExit = $LASTEXITCODE
& git pull origin main --ff-only --quiet 2>&1 | Out-Null
$pullExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'

if ($fetchExit -ne 0 -or $pullExit -ne 0) {
    Add-Content -Path $log -Value "=== $stamp UYARI: git tazeleme basarisiz (fetch=$fetchExit pull=$pullExit) - depo guncel olmayabilir ==="
}

# --- asil kontrol ---
$ErrorActionPreference = 'Continue'
$output = & python scripts\pablo_drift.py 2>&1 | Out-String
$exitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'

Add-Content -Path $log -Value "=== $stamp (exit $exitCode) ==="
Add-Content -Path $log -Value $output

if ($exitCode -ne 0) {
    $msg = "Pablo drift uyarisi ($stamp):`n$output`nKaynak: C:\CyberGene\HermesNode vs jeff_repo/pablo/. Inceleyip gerekirse 'python scripts\pablo_drift.py --sync' ile git'e kopyala, sonra gozden gecirip commit et."
    $msg | ssh hermes "python3 /home/hermes/scripts/send_alert.py"
}
