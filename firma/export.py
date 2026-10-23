"""Bundle graph-ingestion artifacts for downstream repositories."""

from __future__ import annotations

import shutil
from pathlib import Path


def export_ingestion(
    observations_dir: Path | str = "outputs/part2/observations",
    source_manifest_path: Path | str = "outputs/part2/source_manifest.json",
    links_path: Path | str = "outputs/part3/links.jsonl",
    profiles_path: Path | str = "outputs/part4/profiles.jsonl",
    output_dir: Path | str = "outputs/ingestion",
) -> Path:
    """Copy canonical graph inputs into a portable, stable directory layout."""
    observations_dir = Path(observations_dir)
    source_manifest_path = Path(source_manifest_path)
    links_path = Path(links_path)
    profiles_path = Path(profiles_path)
    output_dir = Path(output_dir)

    required_paths = (observations_dir, source_manifest_path, links_path, profiles_path)
    missing_paths = [path for path in required_paths if not path.exists()]
    if missing_paths:
        missing = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"Cannot export ingestion bundle; missing inputs: {missing}")
    if not observations_dir.is_dir():
        raise NotADirectoryError(f"Observations input is not a directory: {observations_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(observations_dir, output_dir / "observations", dirs_exist_ok=True)
    shutil.copy2(source_manifest_path, output_dir / "source_manifest.json")
    shutil.copy2(links_path, output_dir / "links.jsonl")
    shutil.copy2(profiles_path, output_dir / "profiles.jsonl")
    return output_dir
