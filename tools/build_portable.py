from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST_ROOT = ROOT / "dist"
PACKAGE_DIR = DIST_ROOT / "Evo-XTTS-V2-Windows-Portable"

COPY_FILES = [
    "system/start.py",
    "system/requirements.txt",
    "system/run-xtts.bat",
    "system/setup.bat",
    "system/bootstrap-runtime.ps1",
    "system/bootstrap-ffmpeg.ps1",
    "ui/index.html",
    "docs/doc.html",
    "README.md",
    "start.bat",
    "install.bat",
]

COPY_DIRS = [
    "app",
    ".tts",
    "ffmpeg",
]


PORTABLE_README = """EVO XTTS V2 PORTABLE FOR WINDOWS
=================================

How to use:

1. Place your `.wav` voice files inside the `voices` folder
2. Double-click `start.bat`
3. Wait for the browser to open
4. Use the interface at http://localhost:8881/

Important:

- this version uses the bundled Python runtime inside `runtime`
- ffmpeg is bundled inside `ffmpeg`
- the model cache is already included
- the `voices` folder is intentionally empty so you can add your own voice files
- WAV is the default and recommended format

To close the app:

- close the black console window that remains open
"""


def safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def copy_tree(src: Path, dst: Path, extra_ignore: tuple[str, ...] = ()) -> None:
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            ".pytest_cache",
            ".mypy_cache",
            *extra_ignore,
        ),
    )


def prepare_voices_dir(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    readme = ROOT / "voices" / "README.txt"
    if readme.exists():
        shutil.copy2(readme, dst / "README.txt")
    gitkeep = ROOT / "voices" / ".gitkeep"
    if gitkeep.exists():
        shutil.copy2(gitkeep, dst / ".gitkeep")


def main() -> None:
    runtime_dir = ROOT / "runtime"
    if not runtime_dir.exists():
        runtime_dir = ROOT / "venv"
    tts_cache_dir = ROOT / ".tts"

    if not runtime_dir.exists():
        raise SystemExit("Neither 'runtime' nor 'venv' exists. Run system\\setup.bat before building the portable package.")

    if not tts_cache_dir.exists():
        raise SystemExit("The '.tts' folder does not exist. Start the application once to download the model before building the portable package.")

    DIST_ROOT.mkdir(exist_ok=True)
    safe_rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    for file_name in COPY_FILES:
        src = ROOT / file_name
        if src.exists():
            dst = PACKAGE_DIR / file_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    for dir_name in COPY_DIRS:
        src = ROOT / dir_name
        if src.exists():
            copy_tree(src, PACKAGE_DIR / dir_name)

    prepare_voices_dir(PACKAGE_DIR / "voices")
    copy_tree(runtime_dir, PACKAGE_DIR / "runtime")

    (PACKAGE_DIR / "README.txt").write_text(PORTABLE_README, encoding="utf-8")

    print(f"Portable created at: {PACKAGE_DIR}")
    print("Next step: compress the folder and upload it as a GitHub Release asset.")


if __name__ == "__main__":
    main()
