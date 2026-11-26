param(
    [Parameter(Mandatory)][string]$RsiWorkspace
)

$ErrorActionPreference = 'Stop'
$package = Split-Path -Parent $PSScriptRoot
$workspace = (Resolve-Path -LiteralPath $RsiWorkspace).Path
$backend = Join-Path $workspace 'rsi-skill-spring-boot'
$frontend = Join-Path $workspace 'rsi-skill-platform'
$visual = Join-Path $workspace 'rsi-flow-visual'
foreach ($file in "$backend/pom.xml", "$frontend/next.config.ts", "$visual/package.json") {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing upstream files: $file" }
}

$overlays = @{ backend = $backend; frontend = $frontend }
$copies = foreach ($part in @('backend', 'frontend')) {
    $source = Join-Path $package $part
    foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -File) {
        $relative = $file.FullName.Substring($source.Length + 1)
        $target = Join-Path $overlays[$part] $relative
        if (Test-Path -LiteralPath $target) {
            if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath $target).Hash) {
                throw "Different content already exists: $target. Run in a fresh copy of the upstream repositories."
            }
        } else {
            @{ Source = $file.FullName; Target = $target }
        }
    }
}

$patches = @(
    @{ Repo = $visual; Name = 'visual-build.patch' },
    @{ Repo = $frontend; Name = 'frontend-dependencies.patch' },
    @{ Repo = $frontend; Name = 'frontend-routing.patch' }
)
$pending = foreach ($patch in $patches) {
    $path = Join-Path $package "patches/$($patch.Name)"
    & git -C $patch.Repo apply --reverse --check $path 2>$null
    if ($LASTEXITCODE -eq 0) { continue }
    & git -C $patch.Repo apply --check $path
    if ($LASTEXITCODE -ne 0) { throw "Patch does not match the upstream checkout: $path" }
    @{ Repo = $patch.Repo; Path = $path }
}

foreach ($patch in $pending) {
    & git -C $patch.Repo apply $patch.Path
    if ($LASTEXITCODE -ne 0) { throw "Cannot apply $($patch.Path)" }
}
foreach ($copy in $copies) {
    New-Item -ItemType Directory (Split-Path -Parent $copy.Target) -Force | Out-Null
    Copy-Item -LiteralPath $copy.Source -Destination $copy.Target
}
Write-Output "SkillRet sources installed under $workspace"
