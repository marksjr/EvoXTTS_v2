param(
    [string]$FfmpegDir = "ffmpeg",
    [string]$FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$ffmpegPath = Join-Path $projectRoot $FfmpegDir
$binPath = Join-Path $ffmpegPath "bin"
$tempPath = Join-Path $projectRoot ".ffmpeg-bootstrap"
$zipPath = Join-Path $tempPath "ffmpeg.zip"
$extractPath = Join-Path $tempPath "extract"

Write-Host "Preparing local ffmpeg at $ffmpegPath"

if (Test-Path (Join-Path $binPath "ffmpeg.exe")) {
    Write-Host "Local ffmpeg already exists."
    exit 0
}

if (Test-Path $tempPath) {
    Remove-Item -LiteralPath $tempPath -Recurse -Force
}

New-Item -ItemType Directory -Path $tempPath -Force | Out-Null
New-Item -ItemType Directory -Path $extractPath -Force | Out-Null

try {
    Write-Host "Downloading ffmpeg with curl..."
    & curl.exe -L $FfmpegUrl -o $zipPath
    if ($LASTEXITCODE -ne 0) {
        throw "curl failed while downloading ffmpeg."
    }

    Write-Host "Extracting ffmpeg..."
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force

    $sourceRoot = Get-ChildItem -LiteralPath $extractPath -Directory | Select-Object -First 1
    if (-not $sourceRoot) {
        throw "Could not find the extracted ffmpeg folder."
    }

    if (Test-Path $ffmpegPath) {
        Remove-Item -LiteralPath $ffmpegPath -Recurse -Force
    }

    Move-Item -LiteralPath $sourceRoot.FullName -Destination $ffmpegPath

    if (-not (Test-Path (Join-Path $binPath "ffmpeg.exe"))) {
        throw "ffmpeg.exe was not found after extraction."
    }

    Write-Host "Portable ffmpeg is ready."
}
finally {
    if (Test-Path $tempPath) {
        Remove-Item -LiteralPath $tempPath -Recurse -Force
    }
}
