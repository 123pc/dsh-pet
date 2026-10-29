# Portable data lives beside this script; never install into the user's DSH profile.
[CmdletBinding()]
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$data = Join-Path $PSScriptRoot 'data'
$petRoot = Join-Path $data 'dsh-pet/pet'
$pack = Join-Path $PSScriptRoot 'pet-pack'
$manifest = Get-Content -LiteralPath (Join-Path $pack 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($CheckOnly) {
    . (Join-Path $pack 'Pack.ps1')
    $null = Read-PackManifest
    Write-Host 'PASS portable pack integrity; no configuration changed.'
    return
}
New-Item -ItemType Directory -Path $petRoot -Force | Out-Null
$receiptPath = Join-Path $petRoot 'claude-dafeiyu-install.json'
$installedVersion = $null
if (Test-Path -LiteralPath $receiptPath) {
    $installedVersion = (Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json).version
}
if ($installedVersion -ne $manifest.version) {
    & (Join-Path $pack 'install.ps1') -PetRoot $petRoot
}
$mainPath = Join-Path $data 'dsh-pet/main-config.jsonc'
if (-not (Test-Path -LiteralPath $mainPath)) {
    $main = @{ pets = @(@{ id = 'main'; name = '大肥鱼'; size = 300; display = 'none';
        balanceEnabled = $false; whisperEnabled = $false; workStatusEnabled = $true;
        fixedEnabled = $false; position = @{ corner = 'bottom-right'; marginX = 40; marginY = 24 } }) }
    [IO.File]::WriteAllText($mainPath, ($main | ConvertTo-Json -Depth 12), (New-Object Text.UTF8Encoding $false))
}
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
$executable = Join-Path $PSScriptRoot 'runtime/Claude-Dafeiyu.exe'
# A packaged Electron app parses screen scaling before its async main module loads.
# Pass the helper's Windows default on the initial command line; the DPI probe is
# a fresh child process without this argument and still measures the real scale.
$scaleArguments = @()
if ($env:DSH_PET_FORCE_DSF -ne '0') {
    $forcedScale = 1.0
    $override = 0.0
    if ([double]::TryParse($env:DSH_PET_FORCE_DSF, [ref]$override) -and $override -gt 0) { $forcedScale = $override }
    $scaleArguments = @('--force-device-scale-factor=' + $forcedScale.ToString([Globalization.CultureInfo]::InvariantCulture))
}
if ($scaleArguments.Count) {
    Start-Process -FilePath $executable -ArgumentList $scaleArguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
} else {
    Start-Process -FilePath $executable -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
}
