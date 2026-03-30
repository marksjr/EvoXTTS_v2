# GitHub Upload Checklist

## Repository

- [ ] `venv/` is not committed
- [ ] `.tts/` is not committed
- [ ] `dist/` is not committed
- [ ] no private `.wav` files remain tracked in `voices/`
- [ ] `README.md` is up to date
- [ ] install and troubleshooting docs are present

## Source Build Test

- [ ] `install.bat` works
- [ ] `start.bat` works
- [ ] the interface opens in the browser
- [ ] `/health` returns `ok`
- [ ] WAV generation works
- [ ] streaming generation works

## Portable Release Test

- [ ] `system/build-portable.bat` creates the final package
- [ ] the portable folder runs on a clean machine or environment
- [ ] the model cache is already included in the release
- [ ] the user can run it without manually installing Python