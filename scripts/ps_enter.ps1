Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W2 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
}
"@
Add-Type -AssemblyName System.Windows.Forms

$p = Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output "HATA: WindowsTerminal bulunamadi"; exit 1 }

[W2]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 600

$fg = [W2]::GetForegroundWindow()
if ($fg -ne $p.MainWindowHandle) {
  Write-Output "DURDU: yanlis pencere onde, ENTER BASILMADI"
  exit 1
}

[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep -Milliseconds 800

$fg2 = [W2]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[W2]::GetWindowText($fg2, $sb, 256) | Out-Null
Write-Output "enter_basildi: EVET"
Write-Output ("baslik: " + $sb.ToString())
