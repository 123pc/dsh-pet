# 安装前验证完整性，保留实例偏好并备份；不操作 DSH profile。
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$PetRoot = (Join-Path $env:USERPROFILE '.dsh\dsh-pet\pet'),
    [switch]$CheckOnly
)
$installerCmdlet = $PSCmdlet
. (Join-Path $PSScriptRoot 'Pack.ps1')
$manifest = Read-PackManifest
if (-not (Test-Path -LiteralPath $PetRoot -PathType Container)) { throw "Pet directory not found: $PetRoot" }
$PetRoot = [IO.Path]::GetFullPath($PetRoot)
$prepared = @{}
foreach ($file in $manifest.files) {
    $targetPath = Resolve-PackPath $PetRoot $file.target
    if ($file.source.EndsWith('-config.json')) {
        $config = Get-Content -LiteralPath (Join-Path $PSScriptRoot $file.source) -Raw -Encoding UTF8 | ConvertFrom-Json
        if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
            $existing = Get-Content -LiteralPath $targetPath -Raw -Encoding UTF8 | ConvertFrom-Json
            foreach ($pet in $config.pets) {
                $previous = $existing.pets | Where-Object { $_.id -eq $pet.id } | Select-Object -First 1
                if ($previous) {
                    foreach ($key in @('name', 'display', 'size', 'position', 'fixedEnabled', 'balanceEnabled', 'whisperEnabled', 'workStatusEnabled')) {
                        if ($null -ne $previous.PSObject.Properties[$key]) { $pet.$key = $previous.$key }
                    }
                }
            }
        }
        $prepared[$file.target] = $config
    }
}
Resolve-PackPath $PetRoot $script:ReceiptName | Out-Null
Write-Host "Pack $($manifest.version): SHA256 verified for $(@($manifest.files).Count) files."
if ($CheckOnly) { Write-Host "CheckOnly: no files changed. Destination: $PetRoot"; return }
if (-not $installerCmdlet.ShouldProcess($PetRoot, "Install Claude Dafeiyu $($manifest.version)")) { return }
$targets = @($manifest.files | ForEach-Object { $_.target }) + @($script:ReceiptName)
$backupRoot = Backup-PackFiles $PetRoot $targets
$written = @()
try {
    foreach ($file in $manifest.files) {
        $targetPath = Resolve-PackPath $PetRoot $file.target
        New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
        $written += $file.target
        if ($prepared.ContainsKey($file.target)) { Save-PackJson $targetPath $prepared[$file.target] }
        else { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file.source) -Destination $targetPath -Force }
    }
    $receiptFiles = @($manifest.files | ForEach-Object {
        @{ target = $_.target; sha256 = (Get-FileHash -LiteralPath (Resolve-PackPath $PetRoot $_.target) -Algorithm SHA256).Hash.ToLowerInvariant() }
    })
    $written += $script:ReceiptName
    Save-PackJson (Resolve-PackPath $PetRoot $script:ReceiptName) @{ version = $manifest.version; files = $receiptFiles }
} catch {
    foreach ($name in $written) {
        $targetPath = Resolve-PackPath $PetRoot $name
        $savedPath = Resolve-PackPath $backupRoot $name
        if (Test-Path -LiteralPath $savedPath -PathType Leaf) { Copy-Item -LiteralPath $savedPath -Destination $targetPath -Force }
        elseif (Test-Path -LiteralPath $targetPath -PathType Leaf) { Remove-Item -LiteralPath $targetPath -Force }
    }
    throw
}
Write-Host "Installed in: $PetRoot"
if (Test-Path -LiteralPath $backupRoot) { Write-Host "Backup: $backupRoot" }
Write-Host 'Refresh web and reload desktop. If a newly added form is missing, restart DSH.'
