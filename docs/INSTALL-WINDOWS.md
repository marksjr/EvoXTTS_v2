# Windows Installation

## Option 1: Portable Release

Use the portable GitHub Release if you want the simplest Windows setup.

1. Download the `.zip` release file.
2. Extract the folder.
3. Place at least one `.wav` file inside `voices/`.
4. Run `start.bat`.
5. Wait for the browser to open.

## Option 2: Source Setup

1. Open the project folder.
2. Run `install.bat`.
3. Follow the numbered installer steps shown on screen.
4. If the install fails, open `logs/install.log` to see the exact command output for the failed step.
5. When setup finishes, place at least one `.wav` file inside `voices/`.
6. Run `start.bat`.

## Installer Steps

The source installer is intentionally split into visible steps so non-technical users can identify the failure point:

1. Prepare Python environment.
2. Upgrade pip tools.
3. Install PyTorch.
4. Install Evo XTTS dependencies.
5. Validate environment.
6. Prepare ffmpeg for MP3.

## What To Expect On First Launch

The first launch can take a while because the project may need to:

- download the XTTS model
- initialize CUDA or CPU execution
- scan and cache voice samples from `voices/`

The browser should only open when the local API is ready.
If startup fails, check `logs/start.log`.

## MP3 Support

MP3 export uses the local `ffmpeg/` folder when needed. If that download fails, run `install.bat` again and review step 6 in `logs/install.log`.
