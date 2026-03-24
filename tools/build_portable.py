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
    "ui/index.html",
    "docs/ajuda.html",
    "README.md",
    "Abrir XTTS.bat",
    "Instalar XTTS.bat",
]

COPY_DIRS = [
    "app",
    ".tts",
]


PORTABLE_README = """EVO XTTS V2 PORTABLE PARA WINDOWS
=================================

Como usar:

1. Coloque seus arquivos .wav dentro da pasta voices
2. Clique duas vezes em "Abrir XTTS.bat"
3. Aguarde o navegador abrir
4. Use a interface em http://localhost:8881/

Importante:

- Esta versao usa o runtime Python incluido na pasta runtime
- O cache do modelo ja acompanha a release
- A pasta voices vai vazia para voce adicionar sua propria voz
- Se quiser MP3, instale ffmpeg
- O formato WAV funciona como padrao e e o recomendado

Para encerrar:

- Feche a janela preta que ficou aberta
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
    runtime_dir = ROOT / "venv"
    tts_cache_dir = ROOT / ".tts"

    if not runtime_dir.exists():
        raise SystemExit("A pasta 'venv' nao existe. Execute system\setup.bat antes de gerar o portable.")

    if not tts_cache_dir.exists():
        raise SystemExit("A pasta '.tts' nao existe. Inicie a aplicacao uma vez para baixar o modelo antes de gerar o portable.")

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

    (PACKAGE_DIR / "LEIA-ME.txt").write_text(PORTABLE_README, encoding="utf-8")

    print(f"Portable criado em: {PACKAGE_DIR}")
    print("Proximo passo: compacte a pasta e envie como release do GitHub.")


if __name__ == "__main__":
    main()
