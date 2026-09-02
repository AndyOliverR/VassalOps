"""Download and apply GitHub Release zips while preserving duties + config."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from typing import Any, Callable, Dict, Optional, Tuple

import requests


PENDING_DIR = os.path.join("storage", "pending_update")
PRODUCT_REPO_DEFAULT = "AndyOliverR/VassalOps"


def _workspace_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def pending_dir(root: str) -> str:
    return os.path.join(root, PENDING_DIR)


def pending_manifest_path(root: str) -> str:
    return os.path.join(pending_dir(root), "manifest.json")


def read_app_version(root: str) -> str:
    path = os.path.join(root, "VERSION")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip() or "0.0.0"
    except Exception:
        return "0.0.0"


def parse_version(raw: str) -> Tuple[int, int, int]:
    clean = (raw or "").lstrip("v").strip()
    parts = clean.split(".")
    nums = []
    for i in range(3):
        piece = parts[i] if i < len(parts) else "0"
        piece = piece.split("-")[0].split("+")[0]
        try:
            nums.append(int(piece))
        except ValueError:
            nums.append(0)
    return nums[0], nums[1], nums[2]


def is_newer_version(candidate: str, current: str) -> bool:
    return parse_version(candidate) > parse_version(current)


def _github_headers(token: str = "") -> Dict[str, str]:
    headers = {
        "User-Agent": "VassalOps-Updater",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tok = (token or "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def fetch_latest_release(
    repo: str,
    *,
    token: str = "",
    get: Optional[Callable[..., Any]] = None,
    timeout: float = 12.0,
) -> Tuple[bool, str, Dict[str, Any]]:
    repo_s = (repo or "").strip().strip("/")
    if repo_s.count("/") != 1:
        return False, "product repo must look like owner/name", {}
    url = f"https://api.github.com/repos/{repo_s}/releases/latest"
    http_get = get or requests.get
    try:
        resp = http_get(url, headers=_github_headers(token), timeout=timeout)
        code = int(getattr(resp, "status_code", 0))
        if code == 404:
            return False, "No GitHub release published yet.", {}
        if not (200 <= code < 300):
            return False, f"GitHub Releases check failed (HTTP {code}).", {}
        data = resp.json() if callable(getattr(resp, "json", None)) else {}
        if not isinstance(data, dict):
            return False, "GitHub Releases payload was not JSON.", {}
        return True, "", data
    except Exception as exc:
        return False, f"GitHub Releases unreachable: {exc}", {}


def find_release_zip_url(release: Dict[str, Any], version: str) -> str:
    want = {f"VassalOps-{version}.zip", f"VassalOps-v{version}.zip"}
    for asset in release.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        if name in want and url:
            return url
    for asset in release.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        if name.startswith("VassalOps-") and name.endswith(".zip") and url:
            return url
    return str(release.get("zipball_url") or "")


def _resolve_extracted_root(extract_dir: str) -> str:
    if os.path.isfile(os.path.join(extract_dir, "app.py")):
        return extract_dir
    try:
        kids = [os.path.join(extract_dir, n) for n in os.listdir(extract_dir)]
    except Exception:
        return extract_dir
    for kid in kids:
        if os.path.isdir(kid) and os.path.isfile(os.path.join(kid, "app.py")):
            return kid
    return extract_dir


def apply_extracted_update(src: str, root: str, new_version: str) -> None:
    """Overlay product files; keep config.json, config.local.json, and user storage."""
    preserve = tempfile.mkdtemp(prefix="vassalops-preserve-")
    try:
        config_path = os.path.join(root, "config.json")
        local_config_path = os.path.join(root, "config.local.json")
        if os.path.isfile(config_path):
            shutil.copy2(config_path, os.path.join(preserve, "config.json"))
        had_local = os.path.isfile(local_config_path)
        if had_local:
            shutil.copy2(local_config_path, os.path.join(preserve, "config.local.json"))
        storage_src = os.path.join(root, "storage")
        if os.path.isdir(storage_src):
            shutil.copytree(storage_src, os.path.join(preserve, "storage"), dirs_exist_ok=True)

        skip_files = {"config.json"}
        if had_local:
            skip_files.add("config.local.json")

        for name in os.listdir(src):
            if name == ".git":
                continue
            from_path = os.path.join(src, name)
            dest = os.path.join(root, name)
            if os.path.isdir(from_path):
                if name == "storage":
                    continue
                if os.path.isdir(dest):
                    shutil.rmtree(dest)
                shutil.copytree(from_path, dest)
            else:
                if name in skip_files:
                    continue
                shutil.copy2(from_path, dest)

        restored = os.path.join(root, "storage")
        preserved_storage = os.path.join(preserve, "storage")
        if os.path.isdir(preserved_storage):
            if os.path.isdir(restored):
                shutil.rmtree(restored)
            shutil.copytree(preserved_storage, restored)
        elif not os.path.isdir(restored):
            os.makedirs(restored, exist_ok=True)

        new_storage = os.path.join(src, "storage")
        for rel in ("dashboard", os.path.join("duties", "packs")):
            from_rel = os.path.join(new_storage, rel)
            to_rel = os.path.join(restored, rel)
            if os.path.isdir(from_rel):
                os.makedirs(to_rel, exist_ok=True)
                for item in os.listdir(from_rel):
                    src_item = os.path.join(from_rel, item)
                    dest_item = os.path.join(to_rel, item)
                    if os.path.isdir(src_item):
                        if os.path.isdir(dest_item):
                            shutil.rmtree(dest_item)
                        shutil.copytree(src_item, dest_item)
                    else:
                        shutil.copy2(src_item, dest_item)

        saved_config = os.path.join(preserve, "config.json")
        if os.path.isfile(saved_config):
            shutil.copy2(saved_config, config_path)

        saved_local = os.path.join(preserve, "config.local.json")
        if os.path.isfile(saved_local):
            shutil.copy2(saved_local, local_config_path)
        elif not os.path.isfile(local_config_path):
            src_local = os.path.join(src, "config.local.json")
            if os.path.isfile(src_local):
                shutil.copy2(src_local, local_config_path)

        with open(os.path.join(root, "VERSION"), "w", encoding="utf-8", newline="") as f:
            f.write(new_version)
    finally:
        shutil.rmtree(preserve, ignore_errors=True)


def download_zip(url: str, dest_zip: str, timeout: float = 120.0) -> None:
    with requests.get(url, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        with open(dest_zip, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)


def extract_zip(zip_path: str, extract_dir: str) -> str:
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    return _resolve_extracted_root(extract_dir)


def stage_pending_update(root: str, zip_url: str, version: str) -> Dict[str, Any]:
    dest = pending_dir(root)
    os.makedirs(dest, exist_ok=True)
    zip_path = os.path.join(dest, "release.zip")
    download_zip(zip_url, zip_path)
    manifest = {
        "version": version,
        "zip_path": zip_path,
        "zip_url": zip_url,
        "staged_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(pending_manifest_path(root), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def load_pending_manifest(root: str) -> Optional[Dict[str, Any]]:
    path = pending_manifest_path(root)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def clear_pending(root: str) -> None:
    dest = pending_dir(root)
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)


def apply_pending_update(root: str) -> Dict[str, Any]:
    manifest = load_pending_manifest(root)
    if not manifest:
        return {"ok": True, "skipped": True, "reason": "no_pending"}
    zip_path = str(manifest.get("zip_path") or "")
    version = str(manifest.get("version") or "").strip()
    if not zip_path or not os.path.isfile(zip_path) or not version:
        clear_pending(root)
        return {"ok": False, "skipped": False, "reason": "pending_corrupt"}
    work = tempfile.mkdtemp(prefix="vassalops-pending-")
    try:
        src = extract_zip(zip_path, work)
        apply_extracted_update(src, root, version)
        clear_pending(root)
        return {"ok": True, "skipped": False, "applied": True, "version": version}
    except Exception as exc:
        return {"ok": False, "skipped": False, "reason": str(exc)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def apply_release_zip(root: str, zip_url: str, version: str) -> Dict[str, Any]:
    work = tempfile.mkdtemp(prefix="vassalops-update-")
    try:
        zip_path = os.path.join(work, "release.zip")
        download_zip(zip_url, zip_path)
        src = extract_zip(zip_path, os.path.join(work, "extract"))
        apply_extracted_update(src, root, version)
        return {"ok": True, "applied": True, "version": version}
    except Exception as exc:
        return {"ok": False, "applied": False, "reason": str(exc)}
    finally:
        shutil.rmtree(work, ignore_errors=True)
