<#
Pulls the newest Jeff server backup to this PC so that a dead server cannot take the backups with it.

- Rechecks the content hash even when an archive of the same size is already here.
- Downloads to a .part file, checks the size and the SHA-256 against the server, then renames it.
- Keeps the newest -Keep archives locally (default 3).
- After a verified copy it touches ~/backups/.offsite-copy-ok on the server; the watchdog nags when that marker gets old.
- Never deletes anything on the server. Log: <Dest>\pull.log
#>
param(
    [string]$Server = 'hermes',
    [string]$User = '',
    [string]$Dest = 'C:\CyberGene\ServerBackups',
    [ValidateRange(1,30)][int]$Keep = 3
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $Dest | Out-Null
$log = Join-Path $Dest 'pull.log'
function Log($message) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $message" | Add-Content -Path $log -Encoding UTF8 }

# The archives hold configs, tokens and memory: only this account (and SYSTEM) may read the folder.
# Grant by SID, never by name: a name that fails to resolve silently locks everybody out of the folder.
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls $Dest /inheritance:r /grant:r "*${sid}:(OI)(CI)F" "*S-1-5-18:(OI)(CI)F" | Out-Null
try { $null = Get-ChildItem $Dest -ErrorAction Stop } catch { throw "Backup folder is not readable after setting permissions: $Dest" }

# .NET directly: Get-FileHash is missing in some hosted PowerShell sessions.
function Get-Sha256([string]$path) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($path)
    try { return ([System.BitConverter]::ToString($sha.ComputeHash($stream)) -replace '-', '').ToLower() }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Assert-BackupMetadata([string]$Name, [string]$Size, [string]$Hash, [string]$Modified) {
    if ($Name -notmatch '^jeff-backup-\d{8}-\d{6}\.tar\.gz$' -or $Size -notmatch '^\d+$' -or [int64]$Size -le 0 -or $Hash -notmatch '^[a-f0-9]{64}$' -or $Modified -notmatch '^\d+$') { throw 'Invalid backup metadata' }
}
function Test-VerifiedBackup([string]$Path, [long]$Size, [string]$Hash) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $item = Get-Item -LiteralPath $Path
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return $false }
    return $item.Length -eq $Size -and (Get-Sha256 $Path) -eq $Hash
}
function Assert-BackupPath([string]$Path, [string]$Root) {
    $base = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    $directory = [IO.DirectoryInfo]$base
    while ($directory) {
        if ($directory.Exists -and ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Redirected backup directory' }
        $directory = $directory.Parent
    }
    $full = [IO.Path]::GetFullPath($Path)
    if ([IO.Path]::GetDirectoryName($full).TrimEnd('\') -ne $base) { throw 'Backup target escaped its directory' }
    if ((Test-Path -LiteralPath $Path) -and (((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'Redirected backup target' }
}

$sshOptions = @('-o', 'BatchMode=yes', '-o', 'ClearAllForwardings=yes', '-o', 'ConnectTimeout=20')
$target = if ($User) { "$User@$Server" } else { $Server }

function Invoke-Remote([string]$script) {
    # PowerShell appends CRLF when piping a string; a trailing comment line keeps that CR out of the last real command
    # (it once turned a marker file name into '.offsite-copy-ok<CR>').
    $text = ($script -replace "`r`n", "`n") + "`n# end"
    $out = $text | ssh @sshOptions $target 'bash -s'
    if ($LASTEXITCODE -ne 0) { throw "ssh failed (exit $LASTEXITCODE)" }
    return $out
}

try {
    $line = Invoke-Remote @'
f=$(ls -1t /home/hermes/backups/jeff-backup-*.tar.gz 2>/dev/null | head -1)
[ -n "$f" ] || { echo "NONE"; exit 0; }
echo "$(basename "$f") $(stat -c %s "$f") $(sha256sum "$f" | cut -d' ' -f1) $(stat -c %Y "$f")"
'@
    $line = ($line | Select-Object -Last 1).Trim()
    if ($line -eq 'NONE') { throw 'no backup archive on the server' }
    $name, $size, $hash, $modified = $line -split ' '
    Assert-BackupMetadata $name $size $hash $modified
    $final = Join-Path $Dest $name
    Assert-BackupPath $final $Dest

    if (Test-VerifiedBackup $final ([int64]$size) $hash) {
        Log "already have $name, nothing to download"
    } else {
        $part = "$final.part"
        Assert-BackupPath $part $Dest
        Remove-Item -LiteralPath $part -ErrorAction SilentlyContinue
        Log "downloading $name ($([math]::Round([int64]$size / 1MB)) MB)"
        & scp @sshOptions "${target}:/home/hermes/backups/$name" $part
        if ($LASTEXITCODE -ne 0) { throw "scp failed (exit $LASTEXITCODE)" }
        if ((Get-Item $part).Length -ne [int64]$size) { throw 'size mismatch after download' }
        $local = Get-Sha256 $part
        if ($local -ne $hash) { Remove-Item -LiteralPath $part; throw 'SHA-256 mismatch after download' }
        Move-Item -LiteralPath $part -Destination $final -Force
        Log "verified and stored $name"
    }

    if (!(Test-VerifiedBackup $final ([int64]$size) $hash)) { throw 'Final local copy is not verified' }
    $receipt = @{ version = 1; archive = $name; archive_bytes = [int64]$size; archive_sha256 = $hash; server_mtime_seconds = [int64]$modified; client_hash_verified = $true; verified_at = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() } | ConvertTo-Json -Compress
    Invoke-Remote "umask 077`nprintf '%s\n' '$receipt' > /home/hermes/backups/.offsite-copy-pending`nmv /home/hermes/backups/.offsite-copy-pending /home/hermes/backups/.offsite-copy-ok" | Out-Null

    $old = Get-ChildItem $Dest -Filter 'jeff-backup-*.tar.gz' | Sort-Object LastWriteTime -Descending | Select-Object -Skip $Keep
    foreach ($file in $old) {
        Assert-BackupPath $file.FullName $Dest
        if ($file.Name -notmatch '^jeff-backup-\d{8}-\d{6}\.tar\.gz$') { throw 'Unknown retention target' }
        Remove-Item -LiteralPath $file.FullName; Log "removed old local copy $($file.Name)"
    }
    Log "done; local copies: $((Get-ChildItem $Dest -Filter 'jeff-backup-*.tar.gz').Count)"
    exit 0
} catch {
    Log "FAILED: $($_.Exception.Message)"
    exit 1
}
