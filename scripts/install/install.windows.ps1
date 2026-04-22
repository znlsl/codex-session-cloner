param(
    [switch] $Editable,
    [switch] $Force,
    [Alias("h")]
    [switch] $Help,
    [string] $Python
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$venvDir = if ($env:VENV_DIR) { $env:VENV_DIR } else { Join-Path $projectRoot ".venv" }

function Show-Usage {
    @"
Usage: .\install.ps1 [-Editable] [-Force] [-Python <python-bin>]

Options:
  -Editable        Install in editable mode for local development
  -Force           Recreate the local .venv before installing
  -Python <bin>    Use a specific Python executable
"@
}

function Resolve-PythonCommand {
    param([string] $PreferredPython)

    if ($PreferredPython) {
        return ,@($PreferredPython)
    }
    if (Get-Command "python" -ErrorAction SilentlyContinue) { return ,@("python") }
    if (Get-Command "py" -ErrorAction SilentlyContinue) { return ,@("py", "-3") }
    if (Get-Command "python3" -ErrorAction SilentlyContinue) { return ,@("python3") }
    return $null
}

function Assert-LastExitCode {
    param([string] $StepName)

    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE."
    }
}

if ($Help) {
    Show-Usage
    exit 0
}

$pyCmd = Resolve-PythonCommand -PreferredPython $Python
if (-not $pyCmd) {
    Write-Host "Error: Python not found. Install Python 3 first." -ForegroundColor Red
    exit 127
}

if ($Force -and (Test-Path $venvDir)) {
    Remove-Item -Recurse -Force $venvDir
}

$pythonExe = $pyCmd[0]
$pythonPreArgs = @()
if ($pyCmd.Length -gt 1) {
    $pythonPreArgs = $pyCmd[1..($pyCmd.Length - 1)]
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " AI CLI Kit - Installer (Windows)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Project:   $projectRoot"
Write-Host "Python:    $pythonExe $($pythonPreArgs -join ' ')"
Write-Host "Venv:      $venvDir"
if ($Editable) {
    Write-Host "Mode:      editable"
} else {
    Write-Host "Mode:      standard"
}

# Drop --system-site-packages: it lets a stale system setuptools<61 leak in
# and silently build an empty UNKNOWN-0.0.0 wheel because the PEP 621 [project]
# table goes unread. Our package has zero runtime deps so an isolated venv
# is strictly safer.
& $pythonExe @pythonPreArgs -m venv $venvDir
Assert-LastExitCode "python -m venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Error: failed to create local venv at $venvDir" -ForegroundColor Red
    exit 1
}

# Force-upgrade pip / setuptools / wheel inside the venv so PEP 621 metadata
# is read correctly and console scripts (aik / cst / cc-clean) actually land.
Write-Host "Upgrading pip / setuptools / wheel in the local venv..."
& $venvPython -m pip install --quiet --upgrade pip setuptools wheel
Assert-LastExitCode "pip install --upgrade pip setuptools wheel"

if ($Editable) {
    & $venvPython -m pip install --no-deps -e $projectRoot
} else {
    & $venvPython -m pip install --no-deps $projectRoot
}
Assert-LastExitCode "pip install"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host " Install complete." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "推荐：在项目目录里直接运行 launcher"
Write-Host "  .\aik.cmd                # 顶层菜单（推荐入口，进 Codex / Claude 选一个）"
Write-Host "  .\codex-session-toolkit.cmd"
Write-Host "  .\cc-clean.cmd"
Write-Host ""
Write-Host "如需在任意目录用裸命令 ``aik`` 启动，把 venv Scripts 加入 PATH："
Write-Host "  `$env:Path = `"$venvDir\Scripts;`" + `$env:Path"
Write-Host ""
Write-Host "查看版本："
Write-Host "  .\aik.cmd --version"
