# Publishing On GitHub

## Recommended Distribution Model

For non-technical users, publish the portable release.
Do not rely on the raw source repository as the primary distribution channel.

## Recommended Workflow

1. Run `install.bat`.
2. Run `start.bat` and wait until the model is fully loaded.
3. Confirm the interface opens and audio generation works.
4. Close the application.
5. Run `system/build-portable.bat`.
6. Take the folder `dist/Evo-XTTS-V2-Windows-Portable`.
7. Compress it as a `.zip` file.
8. Upload that `.zip` file to GitHub Releases.

## What The Portable Release Should Include

- bundled Python runtime
- application source files
- web interface
- local model cache in `.tts`
- an empty `voices/` folder or placeholder files only
- `start.bat` and `install.bat`

## What Should Not Be Committed To The Repository

- `venv/`
- `.tts/`
- `dist/`
- private voice files in `voices/*.wav`
- generated test audio
- temporary local files and logs

## Release Description Checklist

Include:

- minimum system requirements
- short setup and usage steps
- a note that the first load may take time
- a note that WAV is the recommended output format