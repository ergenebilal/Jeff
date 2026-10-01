Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W3 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
}
"@
Add-Type -AssemblyName System.Windows.Forms

$p = Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output "HATA: WindowsTerminal bulunamadi"; exit 1 }

[W3]::ShowWindow($p.MainWindowHandle, 9) | Out-Null
Start-Sleep -Milliseconds 400
[W3]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 700

$fg = [W3]::GetForegroundWindow()
if ($fg -ne $p.MainWindowHandle) {
  Write-Output "DURDU: pencere one gelmedi, YAZILMADI"
  exit 1
}

[System.Windows.Forms.SendKeys]::SendWait("{ESC}")
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait("2.5'i yap. Bitince haber ver.")
Start-Sleep -Milliseconds 500

$fg2 = [W3]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[W3]::GetWindowText($fg2, $sb, 256) | Out-Null
Write-Output "yazildi: EVET"
Write-Output ("hala_dogru_pencere: " + ($fg2 -eq $p.MainWindowHandle))
