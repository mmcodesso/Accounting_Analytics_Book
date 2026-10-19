#!/usr/bin/env python3
"""Install EPUBCheck (and a Java runtime when there is none) under outputs/tools/, for the EPUB check.

    python scripts/install_epubcheck.py            # EPUBCheck, plus Java when `java` cannot be found
    python scripts/install_epubcheck.py --force    # download again

EPUBCheck is the validator that distributors such as Draft2Digital run on an uploaded EPUB, so scripts/ebook_validate.py
(and with it scripts/build_ebooks.py, scripts/build_all.py and release.py publish) runs it whenever it can find it.
Nothing is installed on the system: the files go to outputs/tools/ (untracked), and deleting that folder removes them.

    EPUBCheck  the latest release of https://github.com/w3c/epubcheck, checked against the SHA-256 GitHub publishes
    Java       Eclipse Temurin 17 (a JRE), from https://api.adoptium.net, used only for EPUBCheck
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TOOLS = ROOT / "outputs" / "tools"
EPUBCHECK_API = "https://api.github.com/repos/w3c/epubcheck/releases/latest"
TEMURIN = "https://api.adoptium.net/v3/binary/latest/17/ga/{os}/{arch}/jre/hotspot/normal/eclipse?project=jdk"


def fetch(url: str, target: Path) -> str:
    """Download `url` to `target`; return its SHA-256."""
    request = urllib.request.Request(url, headers={"User-Agent": "accounting-analytics-build"})
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as out:
        for chunk in iter(lambda: response.read(1 << 20), b""):
            digest.update(chunk)
            out.write(chunk)
    return digest.hexdigest()


def extract(archive: Path, destination: Path) -> None:
    """Unpack a ZIP, refusing any entry that would land outside the destination."""
    destination.mkdir(parents=True, exist_ok=True)
    base = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for name in zipped.namelist():
            if not (base / name).resolve().is_relative_to(base):
                raise RuntimeError(f"{archive.name} holds an entry outside its folder: {name}")
        zipped.extractall(destination)


def install_epubcheck(force: bool) -> Path:
    from scripts.ebook_validate import find_epubcheck_jar
    existing = find_epubcheck_jar()
    if existing and not force and TOOLS in existing.parents:
        print(f"EPUBCheck is installed: {existing}")
        return existing
    with urllib.request.urlopen(urllib.request.Request(EPUBCHECK_API, headers={"User-Agent": "accounting-analytics-build"}),
                                timeout=60) as response:
        release = json.load(response)
    assets = [a for a in release["assets"] if a["name"].startswith("epubcheck-") and a["name"].endswith(".zip")]
    if not assets:
        raise RuntimeError(f"The latest EPUBCheck release ({release.get('tag_name')}) has no zip file.")
    asset = assets[0]
    expected = (asset.get("digest") or "").removeprefix("sha256:")
    destination = TOOLS / "epubcheck"
    with tempfile.TemporaryDirectory(prefix="epubcheck-") as temp:
        archive = Path(temp) / asset["name"]
        print(f"Downloading {asset['name']} ({release['tag_name']}) ...")
        actual = fetch(asset["browser_download_url"], archive)
        if expected and actual != expected:
            raise RuntimeError(f"{asset['name']} does not match the SHA-256 GitHub publishes for it.")
        if destination.exists():
            shutil.rmtree(destination)
        extract(archive, destination)
    jar = next(destination.rglob("epubcheck.jar"), None)
    if jar is None:
        raise RuntimeError("The EPUBCheck archive holds no epubcheck.jar.")
    print(f"EPUBCheck installed: {jar}")
    return jar


def install_java(force: bool) -> Path | None:
    from scripts.ebook_validate import find_java
    existing = find_java()
    if existing and not force:
        print(f"Java is available: {existing}")
        return Path(existing)
    system = {"Windows": "windows", "Linux": "linux", "Darwin": "mac"}.get(platform.system())
    arch = {"AMD64": "x64", "x86_64": "x64", "arm64": "aarch64", "aarch64": "aarch64"}.get(platform.machine())
    if not (system and arch):
        raise RuntimeError(f"No Java download is known for {platform.system()} {platform.machine()}; install Java 11 or later.")
    destination = TOOLS / "jre"
    with tempfile.TemporaryDirectory(prefix="jre-") as temp:
        archive = Path(temp) / "jre.zip"
        if system != "windows":
            raise RuntimeError("Install Java 11 or later with your package manager (the download here is a ZIP for Windows).")
        print("Downloading a Java runtime (Eclipse Temurin 17) ...")
        fetch(TEMURIN.format(os=system, arch=arch), archive)
        if destination.exists():
            shutil.rmtree(destination)
        extract(archive, destination)
    java = find_java()
    if java is None:
        raise RuntimeError("The Java archive holds no java executable.")
    print(f"Java installed: {java}")
    return Path(java)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="Download again even when installed.")
    parser.add_argument("--no-java", action="store_true", help="Install only EPUBCheck.")
    args = parser.parse_args(argv)
    try:
        install_epubcheck(args.force)
        if not args.no_java:
            install_java(args.force)
    except (RuntimeError, OSError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Done. scripts/ebook_validate.py finds both under outputs/tools/ on its own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
