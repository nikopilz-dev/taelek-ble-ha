$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$release = Invoke-RestMethod 'https://api.github.com/repos/SymbioticSec/hermes-decomp/releases/latest'
$asset = $release.assets | Where-Object { $_.name -match '(windows|pc-windows)' -and $_.name -match '(zip|exe)$' } | Select-Object -First 1
if (-not $asset) { throw 'No Windows binary found in latest release' }
$destination = Join-Path $PSScriptRoot 'hermes-decomp-download'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$archive = Join-Path $destination $asset.name
Invoke-WebRequest $asset.browser_download_url -OutFile $archive
if ($archive.EndsWith('.zip')) { Expand-Archive -LiteralPath $archive -DestinationPath $destination -Force }
$metadata = @{ version = $release.tag_name; asset = $asset.name; url = $asset.browser_download_url; sha256 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash }
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'evidence/hermes-tool.json')
$metadata | ConvertTo-Json
