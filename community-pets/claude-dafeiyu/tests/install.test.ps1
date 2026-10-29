# 用隔离目录验证安装、升级、只检查和卸载；从不访问真实 DSH 配置。
$ErrorActionPreference = 'Stop'
$pack = Split-Path -Parent $PSScriptRoot
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('dsh-pet-test-' + [guid]::NewGuid().ToString('N'))
$petRoot = Join-Path $testRoot 'pet'
New-Item -ItemType Directory -Path $petRoot -Force | Out-Null
function Assert-That($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
& (Join-Path $pack 'install.ps1') -PetRoot $petRoot -CheckOnly
Assert-That (@(Get-ChildItem -LiteralPath $petRoot -Force).Count -eq 0) 'CheckOnly wrote files'
& (Join-Path $pack 'install.ps1') -PetRoot $petRoot -WhatIf
Assert-That (@(Get-ChildItem -LiteralPath $petRoot -Force).Count -eq 0) 'WhatIf wrote files'
& (Join-Path $pack 'install.ps1') -PetRoot $petRoot
$configPath = Join-Path $petRoot 'claude-dafeiyu-config.json'
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$config.pets[0].display = 'desktop'
$config.pets[0].size = 444
$config | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $configPath -Encoding UTF8
& (Join-Path $pack 'install.ps1') -PetRoot $petRoot
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-That ($config.pets[0].display -eq 'desktop' -and $config.pets[0].size -eq 444) 'Upgrade lost user preferences'
$sourceConfig = Get-Content -LiteralPath (Join-Path $pack 'claude-dafeiyu-config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-That (($config.animations.events.balance -join '|') -eq ($sourceConfig.animations.events.balance -join '|')) 'Upgrade did not install the current balance action pool'
$unrelated = Join-Path $petRoot 'other-config.json'
Set-Content -LiteralPath $unrelated -Value 'unrelated' -Encoding UTF8
$unknown = Join-Path $petRoot 'claude-dafeiyu-animation\custom.txt'
Set-Content -LiteralPath $unknown -Value 'custom file' -Encoding UTF8
& (Join-Path $pack 'uninstall.ps1') -PetRoot $petRoot -CheckOnly
Assert-That (Test-Path -LiteralPath $configPath) 'Uninstall CheckOnly removed config'
$config.pets[0].size = 555
$config | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $configPath -Encoding UTF8
$rejected = $false
try { & (Join-Path $pack 'uninstall.ps1') -PetRoot $petRoot } catch { $rejected = $true }
Assert-That $rejected 'Uninstall did not protect modified config'
Assert-That (Test-Path -LiteralPath $configPath) 'Rejected uninstall changed files'
& (Join-Path $pack 'uninstall.ps1') -PetRoot $petRoot -Force
Assert-That (-not (Test-Path -LiteralPath $configPath)) 'Uninstall left owned config'
Assert-That ((Test-Path -LiteralPath $unknown) -and (Test-Path -LiteralPath $unrelated)) 'Uninstall deleted unrelated files'
Assert-That (@(Get-ChildItem -LiteralPath (Join-Path $petRoot '.claude-dafeiyu-backups') -Recurse -Filter 'claude-dafeiyu-config.json').Count -ge 2) 'Missing backups'
& (Join-Path $pack 'uninstall.ps1') -PetRoot $petRoot
. (Join-Path $pack 'Pack.ps1')
$rejected = $false
try { Resolve-PackPath $petRoot '../outside.webm' | Out-Null } catch { $rejected = $true }
Assert-That $rejected 'Path traversal was accepted'
Write-Host "PASS install/upgrade/CheckOnly/WhatIf/modified-file protection/uninstall/idempotence/path checks. Sandbox retained at $testRoot"
