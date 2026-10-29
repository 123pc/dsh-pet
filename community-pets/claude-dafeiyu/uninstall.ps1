# 只移除本包清单中的文件；修改过的文件需要显式 -Force，并始终先备份。
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$PetRoot = (Join-Path $env:USERPROFILE '.dsh\dsh-pet\pet'),
    [switch]$CheckOnly,
    [switch]$Force
)
$uninstallerCmdlet = $PSCmdlet
. (Join-Path $PSScriptRoot 'Pack.ps1')
$manifest = Read-PackManifest
$PetRoot = [IO.Path]::GetFullPath($PetRoot)
$hashes = @{}
foreach ($file in $manifest.files) { $hashes[$file.target] = $file.sha256 }
$receiptPath = Resolve-PackPath $PetRoot $script:ReceiptName
if (Test-Path -LiteralPath $receiptPath -PathType Leaf) {
    $receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $receipt.files) {
        if ($hashes.ContainsKey($entry.target) -and $entry.sha256 -match '^[0-9a-f]{64}$') { $hashes[$entry.target] = $entry.sha256 }
    }
}
$present = @()
$modified = @()
foreach ($file in $manifest.files) {
    $targetPath = Resolve-PackPath $PetRoot $file.target
    if (-not (Test-Path -LiteralPath $targetPath -PathType Leaf)) { continue }
    $present += $file.target
    if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$file.target]) { $modified += $file.target }
}
Write-Host "Found $($present.Count) pack files; modified: $($modified.Count)."
if ($CheckOnly) { Write-Host 'CheckOnly: no files changed.'; return }
if ($modified.Count -and -not $Force) { throw "Modified files: $($modified -join ', '). Use -Force to back up and uninstall." }
if (-not $present.Count -and -not (Test-Path -LiteralPath $receiptPath)) { Write-Host 'Already uninstalled.'; return }
if (-not $uninstallerCmdlet.ShouldProcess($PetRoot, 'Back up and uninstall Claude Dafeiyu')) { return }
$targets = $present + @($script:ReceiptName)
$backupRoot = Backup-PackFiles $PetRoot $targets
foreach ($name in $targets) {
    $targetPath = Resolve-PackPath $PetRoot $name
    if (Test-Path -LiteralPath $targetPath -PathType Leaf) { Remove-Item -LiteralPath $targetPath -Force }
}
foreach ($name in @('claude-dafeiyu-animation', 'claude-dafeiyu-lean-animation')) {
    $folder = Resolve-PackPath $PetRoot $name
    if ((Test-Path -LiteralPath $folder -PathType Container) -and -not (Get-ChildItem -LiteralPath $folder -Force)) { Remove-Item -LiteralPath $folder }
}
Write-Host "Uninstalled. Backup: $backupRoot"
Write-Host 'Restart DSH to rescan file pets. The sidebar plugin is managed separately.'
