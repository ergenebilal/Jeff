Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
}
"@

$p = Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output "HATA: WindowsTerminal penceresi bulunamadi"; exit 1 }

[W]::ShowWindow($p.MainWindowHandle, 9) | Out-Null
Start-Sleep -Milliseconds 400
[W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 600

$fg = [W]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[W]::GetWindowText($fg, $sb, 256) | Out-Null

Write-Output ("hedef_handle: " + $p.MainWindowHandle)
Write-Output ("one_gelen_handle: " + $fg)
Write-Output ("one_gelen_baslik: " + $sb.ToString())
if ($fg -eq $p.MainWindowHandle) { Write-Output "SONUC: DOGRU_PENCERE_ONE" } else { Write-Output "SONUC: YANLIS_PENCERE" }
