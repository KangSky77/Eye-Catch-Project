[CmdletBinding()]
param([switch]$Apply)

# Only regenerable project caches are eligible. Dependencies, datasets,
# model weights, credentials and other tools' worktrees are never targets.
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$rootPrefix = $projectRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
if ((Get-Item -LiteralPath $projectRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw "Refusing a linked project root: $projectRoot"
}
$targets = @()

foreach ($name in @('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', '.coverage')) {
    $candidate = Join-Path $projectRoot $name
    if (Test-Path -LiteralPath $candidate) { $targets += $candidate }
}
$targets += @(Get-ChildItem -LiteralPath $projectRoot -Directory -Force |
    Where-Object { $_.Name -like '.pytest-tmp*' } | ForEach-Object { $_.FullName })
foreach ($name in @('app', 'scripts', 'tests')) {
    $scope = Join-Path $projectRoot $name
    # Walk explicitly so a junction is never followed during discovery.
    $pending = [Collections.Generic.Stack[string]]::new()
    $pending.Push($scope)
    while ($pending.Count -gt 0) {
        $directory = $pending.Pop()
        if (-not (Test-Path -LiteralPath $directory)) { continue }
        if ((Get-Item -LiteralPath $directory -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
        foreach ($item in Get-ChildItem -LiteralPath $directory -Directory -Force) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
            if ($item.Name -eq '__pycache__') { $targets += $item.FullName }
            else { $pending.Push($item.FullName) }
        }
    }
}

$targets = @($targets | Sort-Object -Unique)
$totalBytes = 0L
foreach ($target in $targets) {
    $absolute = [IO.Path]::GetFullPath($target)
    if (-not $absolute.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target is outside the project: $absolute"
    }
    # Check all ancestors before recursion or removal, including the root.
    $ancestor = $absolute
    while ($true) {
        if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing a linked path: $ancestor"
        }
        if ($ancestor -eq $projectRoot) { break }
        $ancestor = Split-Path -Parent $ancestor
    }
    $item = Get-Item -LiteralPath $absolute -Force
    if ($item.PSIsContainer) {
        $pending = [Collections.Generic.Stack[string]]::new()
        $pending.Push($absolute)
        while ($pending.Count -gt 0) {
            foreach ($child in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
                if ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                    throw "Refusing a linked cache entry: $($child.FullName)"
                }
                if ($child.PSIsContainer) { $pending.Push($child.FullName) }
                else { $totalBytes += $child.Length }
            }
        }
    } else { $totalBytes += $item.Length }
    Write-Output $absolute
}

Write-Output ('{0} cache paths, {1:N2} MB. Mode: {2}' -f $targets.Count, ($totalBytes / 1MB), $(if ($Apply) { 'remove' } else { 'preview' }))
if ($Apply) {
    foreach ($target in $targets) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
} else {
    Write-Output 'No files removed. Run with -Apply when tests and training are idle.'
}
