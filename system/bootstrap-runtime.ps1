param(
    [string]$RuntimeDir = "runtime",
    [string]$PythonVersion = "3.11.9"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $projectRoot $RuntimeDir
$tempPath = Join-Path $projectRoot ".runtime-bootstrap"
$embedZipPath = Join-Path $tempPath "python-embed.zip"
$getPipPath = Join-Path $tempPath "get-pip.py"
$pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "Preparing local Python runtime at $runtimePath"

if (Test-Path (Join-Path $runtimePath "python.exe")) {
    Write-Host "Local runtime already exists."
    exit 0
}

if (Test-Path $tempPath) {
    Remove-Item -LiteralPath $tempPath -Recurse -Force
}

New-Item -ItemType Directory -Path $tempPath -Force | Out-Null
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null

try {
    Write-Host "Downloading embedded Python $PythonVersion..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $embedZipPath

    Write-Host "Extracting runtime..."
    Expand-Archive -LiteralPath $embedZipPath -DestinationPath $runtimePath -Force

    $pthFile = Get-ChildItem -LiteralPath $runtimePath -Filter "python*._pth" | Select-Object -First 1
    if (-not $pthFile) {
        throw "Could not find the python._pth file in the runtime folder."
    }

    $pthLines = Get-Content -LiteralPath $pthFile.FullName
    $updatedLines = foreach ($line in $pthLines) {
        if ($line -match '^\s*#\s*import site\s*$') {
            "import site"
        } else {
            $line
        }
    }

    $requiredEntries = @("Lib", "Lib\site-packages")
    foreach ($entry in $requiredEntries) {
        if ($updatedLines -notcontains $entry) {
            $updatedLines += $entry
        }
    }

    if ($updatedLines -notcontains "import site") {
        $updatedLines += "import site"
    }

    Set-Content -LiteralPath $pthFile.FullName -Value $updatedLines -Encoding ASCII

    New-Item -ItemType Directory -Path (Join-Path $runtimePath "Lib") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $runtimePath "Lib\site-packages") -Force | Out-Null

    Write-Host "Downloading pip bootstrap..."
    Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath

    Write-Host "Installing pip into the local runtime..."
    & (Join-Path $runtimePath "python.exe") $getPipPath --no-warn-script-location

    Write-Host "Portable runtime is ready."
}
finally {
    if (Test-Path $tempPath) {
        Remove-Item -LiteralPath $tempPath -Recurse -Force
    }
}
