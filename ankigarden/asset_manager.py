from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests


class AssetManager:
    def __init__(self, config: Any, storage: Any) -> None:
        self.config = config
        self.storage = storage
        self.metadata = self.storage.load_asset_metadata()
        self.last_request_at = 0.0

    def get_or_fetch(
        self, category: str, key: str, query: str, provider_hint: Optional[str] = None
    ) -> Optional[Path]:
        cache_key = f"{category}:{key}"
        existing = self.metadata.get(cache_key, {})
        cached_path = existing.get("local_path")
        if cached_path:
            p = self.storage.addon_dir / cached_path
            if p.exists():
                return p

        providers = self.config.nested("image_api", "provider_priority", default=[])
        if provider_hint and provider_hint in providers:
            providers = [provider_hint] + [p for p in providers if p != provider_hint]

        for provider in providers:
            result = self._fetch_from_provider(provider, query)
            if not result:
                continue
            url, attribution = result
            local_path = self._download(category, key, url)
            if local_path:
                self.metadata[cache_key] = {
                    "provider": provider,
                    "query": query,
                    "source_url": url,
                    "attribution": attribution,
                    "downloaded_at": int(time.time()),
                    "local_path": str(local_path.relative_to(self.storage.addon_dir)),
                }
                self.storage.save_asset_metadata(self.metadata)
                return local_path
        return None

    def _fetch_from_provider(self, provider: str, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        attempts = self.config.nested("image_api", "max_retries", default=2)
        for _ in range(attempts):
            self._wait_rate_limit()
            try:
                if provider == "unsplash":
                    found = self._from_unsplash(query)
                elif provider == "pexels":
                    found = self._from_pexels(query)
                elif provider == "pixabay":
                    found = self._from_pixabay(query)
                else:
                    found = None
                if found:
                    return found
            except requests.RequestException:
                time.sleep(0.5)
        return None

    def _wait_rate_limit(self) -> None:
        min_gap = float(self.config.nested("image_api", "rate_limit_seconds", default=1.0))
        elapsed = time.time() - self.last_request_at
        if elapsed < min_gap:
            time.sleep(min_gap - elapsed)
        self.last_request_at = time.time()

    def _from_unsplash(self, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        key = self.config.nested("image_api", "unsplash_access_key", default="")
        if not key:
            return None
        timeout = self.config.nested("image_api", "request_timeout_sec", default=8)
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "orientation": "landscape", "per_page": 30},
            headers={"Authorization": f"Client-ID {key}"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("results", [])
        if not data:
            return None
        photo = data[0]
        return (
            photo["urls"]["regular"],
            {
                "author": photo["user"]["name"],
                "author_url": photo["user"]["links"]["html"],
                "page_url": photo["links"]["html"],
            },
        )

    def _from_pexels(self, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        key = self.config.nested("image_api", "pexels_api_key", default="")
        if not key:
            return None
        timeout = self.config.nested("image_api", "request_timeout_sec", default=8)
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 30, "orientation": "landscape"},
            headers={"Authorization": key},
            timeout=timeout,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            return None
        photo = photos[0]
        return (
            photo["src"]["large"],
            {"author": photo.get("photographer"), "page_url": photo.get("url")},
        )

    def _from_pixabay(self, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        key = self.config.nested("image_api", "pixabay_api_key", default="")
        if not key:
            return None
        timeout = self.config.nested("image_api", "request_timeout_sec", default=8)
        resp = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": key,
                "q": query,
                "image_type": "photo",
                "per_page": 30,
                "safesearch": "true",
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        if not hits:
            return None
        hit = hits[0]
        return (
            hit.get("largeImageURL") or hit.get("webformatURL"),
            {"author": hit.get("user"), "page_url": hit.get("pageURL")},
        )

    def _download(self, category: str, key: str, url: str) -> Optional[Path]:
        if not url:
            return None
        timeout = self.config.nested("image_api", "request_timeout_sec", default=8)
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        ext = ".jpg"
        target = self.storage.assets_root / category / f"{key}_{digest}{ext}"
        if target.exists() and target.stat().st_size > 0:
            return target
        target.write_bytes(resp.content)
        return target

    def export_metadata_json(self) -> str:
        return json.dumps(self.metadata, indent=2)
