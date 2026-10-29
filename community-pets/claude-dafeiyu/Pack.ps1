# 角色包文件校验与备份共用逻辑；只允许操作清单列出的两个角色。
$ErrorActionPreference = 'Stop'
$script:PackRoot = $PSScriptRoot
$script:ReceiptName = 'claude-dafeiyu-install.json'

function Resolve-PackPath([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)') { throw "Unsafe relative path: $Relative" }
    $basePath = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    $resolvedPath = [IO.Path]::GetFullPath((Join-Path $basePath $Relative))
    if (-not $resolvedPath.StartsWith($basePath, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes package root: $Relative" }
    $parentPath = Split-Path -Parent $resolvedPath
    while ($parentPath -and $parentPath.Length -ge $basePath.TrimEnd('\', '/').Length) {
        if ((Test-Path -LiteralPath $parentPath) -and ((Get-Item -LiteralPath $parentPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Refusing a directory link: $parentPath"
        }
        $parentPath = Split-Path -Parent $parentPath
    }
    if ((Test-Path -LiteralPath $resolvedPath) -and ((Get-Item -LiteralPath $resolvedPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing a file link: $resolvedPath"
    }
    return $resolvedPath
}

function Read-PackManifest {
    $manifest = Get-Content -LiteralPath (Join-Path $script:PackRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $manifest.version -or -not $manifest.files -or @($manifest.files).Count -eq 0) { throw 'Invalid manifest' }
    $seen = @{}
    foreach ($file in $manifest.files) {
        $allowedConfig = $file.source -match '^claude-dafeiyu(-lean)?-config\.json$'
        $allowedMedia = $file.source -match '^(animation|lean-animation)/[\p{L}\p{N} _\u00B7\uFF0C-]+\.webm$'
        if (-not ($allowedConfig -or $allowedMedia) -or $file.sha256 -notmatch '^[0-9a-f]{64}$') { throw "Invalid manifest entry: $($file.source)" }
        $expected = $file.source -replace '^animation/', 'claude-dafeiyu-animation/' -replace '^lean-animation/', 'claude-dafeiyu-lean-animation/'
        if ($file.target -ne $expected -or $seen.ContainsKey($file.target)) { throw 'Invalid or duplicate target' }
        $seen[$file.target] = $true
        $sourcePath = Resolve-PackPath $script:PackRoot $file.source
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing source: $($file.source)" }
        if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) { throw "SHA256 mismatch: $($file.source)" }
    }
    return $manifest
}

function Save-PackJson([string]$Path, $Value) {
    $json = ConvertTo-Json -InputObject $Value -Depth 60
    [IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, (New-Object Text.UTF8Encoding $false))
}

function Backup-PackFiles([string]$PetRoot, $Targets) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fffffff'
    $backupRoot = Resolve-PackPath $PetRoot ('.claude-dafeiyu-backups/' + $stamp)
    foreach ($targetName in $Targets) {
        $currentPath = Resolve-PackPath $PetRoot $targetName
        if (Test-Path -LiteralPath $currentPath -PathType Leaf) {
            $savedPath = Resolve-PackPath $backupRoot $targetName
            New-Item -ItemType Directory -Path (Split-Path -Parent $savedPath) -Force | Out-Null
            Copy-Item -LiteralPath $currentPath -Destination $savedPath
        }
    }
    return $backupRoot
}
