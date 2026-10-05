"""Check public source and build output for model asset files and references."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


SITE = Path(__file__).resolve().parents[1]
BANNED_SUFFIXES = {
    ".nds", ".arc", ".nsbmd", ".nsbtx", ".nsbca", ".bmd0", ".btx0",
    ".bca0", ".glb", ".gltf", ".bin",
}
TEXT_SUFFIXES = {".html", ".js", ".mjs", ".css", ".astro", ".ts", ".tsx", ".jsx"}
MODEL_REFERENCE = re.compile(
    r"(?i)(?:<model-viewer\b|\.(?:glb|gltf|nsbmd|nsbtx|bmd0|btx0|bca0)(?=[\s\"'<>?#)]|$))"
)


def paths_to_scan() -> list[Path]:
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=SITE, check=True, capture_output=True
    ).stdout
    paths = [SITE / name.decode("utf-8") for name in tracked.split(b"\0") if name]
    for folder in (SITE / "src", SITE / "public", SITE / "dist"):
        if folder.is_dir():
            paths.extend(path for path in folder.rglob("*") if path.is_file())
    return sorted(set(paths))


def main() -> None:
    findings = []
    paths = paths_to_scan()
    for path in paths:
        relative = path.relative_to(SITE).as_posix()
        if path.suffix.lower() in BANNED_SUFFIXES:
            findings.append(f"model/game asset file: {relative}")
        if path.suffix.lower() in TEXT_SUFFIXES:
            content = path.read_text(encoding="utf-8", errors="replace")
            match = MODEL_REFERENCE.search(content)
            if match:
                findings.append(f"model reference in {relative}: {match.group(0)}")
    if findings:
        raise SystemExit("Public asset policy failed:\n" + "\n".join(findings))
    print(f"OK: {len(paths)} public-site files scanned; no model/game asset files or model-viewer references")


if __name__ == "__main__":
    main()
