from __future__ import annotations

from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_ROOT / "workspace"
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_path(path: str | Path) -> Path:
    """Resolve a workspace path and prevent traversal outside workspace."""
    raw = Path(str(path or "."))
    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        parts = list(raw.parts)
        while parts and parts[0].lower() == BASE_DIR.name.lower():
            parts.pop(0)
        candidate = (BASE_DIR.joinpath(*parts)).resolve()

    root = BASE_DIR.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path must stay inside the Shaqs workspace.") from exc
    return candidate


def create_file(filename: str, content: str = "") -> Path:
    file_path = _resolve_path(filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(str(content), encoding="utf-8")
    return file_path


def read_file(filename: str) -> str:
    file_path = _resolve_path(filename)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filename}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Not a file: {filename}")
    return file_path.read_text(encoding="utf-8")


def edit_file(filename: str, new_content: str) -> str:
    file_path = _resolve_path(filename)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filename}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Not a file: {filename}")
    file_path.write_text(str(new_content), encoding="utf-8")
    return f"File updated: {file_path}"


def create_folder(foldername: str) -> Path:
    folder_path = _resolve_path(foldername)
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def list_files(path: str = ".") -> list[Path]:
    root = _resolve_path(path)
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return sorted(root.rglob("*"))


def delete_path(path: str) -> str:
    target = _resolve_path(path)
    if target == BASE_DIR.resolve():
        raise ValueError("Refused to delete the entire workspace.")
    if not target.exists():
        return f"Path not found: {target}"
    if target.is_dir():
        shutil.rmtree(target)
        return f"Folder deleted: {target}"
    target.unlink()
    return f"File deleted: {target}"
