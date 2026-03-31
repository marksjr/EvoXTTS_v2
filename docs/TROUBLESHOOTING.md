# Troubleshooting

## The Browser Opens But The Interface Does Not Respond

Hard refresh the page with `Ctrl+F5`.

## No Voices Appear

Make sure there is at least one `.wav` file inside the `voices/` folder.

## The API Does Not Start

Run `install.bat` again and then try `start.bat`.

## GPU Error

Confirm that `nvidia-smi` works on Windows.
If the GPU is unavailable, the project can fall back to CPU mode.

## MP3 Does Not Work

Run `install.bat` again to restore the local `ffmpeg/` folder.
If it still fails, install ffmpeg manually and retry.

## The First Launch Takes Too Long

This is expected when the model is still being prepared or when voices are being cached for the first time.
