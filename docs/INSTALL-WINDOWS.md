# Windows Installation

## Option 1: Portable Release

Use the portable GitHub Release if you want the simplest Windows setup.

1. Download the `.zip` release file.
2. Extract the folder.
3. Place at least one `.wav` file inside `voices/`.
4. Run `start.bat`.
5. Wait for the browser to open.

## Option 2: Source Setup

1. Install Python 3.11.
2. Open the project folder.
3. Run `install.bat`.
4. When setup finishes, run `start.bat`.

## What To Expect On First Launch

The first launch can take a while because the project may need to:

- load the XTTS model
- initialize CUDA or CPU execution
- scan and cache voice samples from `voices/`

The browser should only open when the local API is ready.

## Optional MP3 Support

If you want MP3 export, install `ffmpeg`:

```powershell
winget install ffmpeg
```