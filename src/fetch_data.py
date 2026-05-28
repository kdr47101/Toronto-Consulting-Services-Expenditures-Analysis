"""Fetch Toronto consulting-services-expenditures resources for 2017-2024.

Writes each resource to data/raw/. Re-running the script overwrites files.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from api_client import download_resource, get_package, get_resource

PACKAGE_ID = "consulting-services-expenditures"
YEARS = range(2017, 2025)
OUTPUT_DIR = Path("data/raw")


def _safe_filename(name: str, default_ext: str = "csv") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._\- ]+", "", name).strip().replace(" ", "_")
    if "." not in cleaned:
        cleaned = f"{cleaned}.{default_ext.lower()}"
    return cleaned


def fetch_consulting_data() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    package = get_package(PACKAGE_ID)
    downloaded: list[Path] = []

    for resource in package["resources"]:
        name = resource.get("name", "")
        if not any(str(y) in name for y in YEARS):
            continue

        print(f"Processing: {name}")
        download_url = resource.get("url")
        if not resource.get("datastore_active", False):
            try:
                meta = get_resource(resource["id"])
                download_url = meta.get("url", download_url)
            except Exception as exc:
                print(f"  resource_show fallback failed: {exc}")

        if not download_url:
            print(f"  no URL for {name}, skipping")
            continue

        ext = resource.get("format", "csv") or "csv"
        dest = OUTPUT_DIR / _safe_filename(name, default_ext=ext)
        try:
            download_resource(download_url, str(dest))
            print(f"  -> {dest}")
            downloaded.append(dest)
        except Exception as exc:
            print(f"  failed: {exc}")

    return downloaded


if __name__ == "__main__":
    files = fetch_consulting_data()
    print(f"\nDownloaded {len(files)} files to {OUTPUT_DIR.resolve()}")
