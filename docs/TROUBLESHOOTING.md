# Troubleshooting

## Installation Fails

Run `install.bat` again and watch the numbered step where it stops.
Then open `logs/install.log` and review the last error lines.

## The Browser Opens But The Interface Does Not Respond

Hard refresh the page with `Ctrl+F5`.

## No Voices Appear

Make sure there is at least one `.wav` file inside the `voices/` folder.

## The API Does Not Start

Run `install.bat` again and then try `start.bat`.
If it still fails, open `logs/start.log`.

## GPU Error

Confirm that `nvidia-smi` works on Windows.
If the GPU is unavailable, the project can fall back to CPU mode.

## MP3 Does Not Work

Run `install.bat` again to restore the local `ffmpeg/` folder.
If it still fails, check step 6 in `logs/install.log` or install ffmpeg manually.

## The First Launch Takes Too Long

This is expected when the model is still being prepared or when voices are being cached for the first time.
