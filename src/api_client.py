"""Thin client for the Toronto Open Data CKAN API.

CKAN docs: https://docs.ckan.org/en/latest/api/
"""
from __future__ import annotations

import requests

BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"


class CKANError(RuntimeError):
    pass


def get_package(package_id: str) -> dict:
    """Return the package (dataset) metadata, including its resources."""
    resp = requests.get(
        f"{BASE_URL}/api/3/action/package_show",
        params={"id": package_id},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise CKANError(f"package_show failed for {package_id}: {payload}")
    return payload["result"]


def get_resource(resource_id: str) -> dict:
    """Return metadata for a single resource."""
    resp = requests.get(
        f"{BASE_URL}/api/3/action/resource_show",
        params={"id": resource_id},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise CKANError(f"resource_show failed for {resource_id}: {payload}")
    return payload["result"]


def download_resource(url: str, dest_path: str) -> None:
    """Stream a resource URL to disk."""
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    fh.write(chunk)
