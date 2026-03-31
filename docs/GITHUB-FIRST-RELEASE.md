# First Release Draft

## Suggested Title

Evo XTTS V2 - Windows Portable v1.0.0

## Release Description

First portable release of Evo XTTS V2 for Windows.

This package was prepared for end users: extract the folder, place a `.wav` file inside `voices/`, run `start.bat`, and wait for the browser to open.

## Included In This Release

- local web interface
- FastAPI backend
- bundled Python runtime
- bundled local `ffmpeg/` folder for MP3 support
- local XTTS model cache already included
- NVIDIA GPU support when available
- CPU fallback when needed

## How To Use

1. Download the `.zip` file.
2. Extract the folder.
3. Place a `.wav` file inside `voices/`.
4. Run `start.bat`.
5. Wait for the browser to open.

## Notes

- WAV is the recommended output format
- MP3 support is already included through the local `ffmpeg/` folder
- the first load can still take a while while the model and voice cache initialize

## Requirements

- Windows 10 or Windows 11
- NVIDIA GPU recommended, but not required
