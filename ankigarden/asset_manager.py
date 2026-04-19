from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Optional

try:
    import requests
except Exception:  # pragma: no cover - fallback for restricted test env
    import json as _json
    from urllib import error as _urlerror
    from urllib import parse as _urlparse
    from urllib import request as _urlrequest

    class _Resp:
        def __init__(self, raw: bytes, status: int) -> None:
            self.content = raw
            self.status_code = status

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise _urlerror.HTTPError(url="", code=self.status_code, msg="http error", hdrs=None, fp=None)

        def json(self) -> dict[str, Any]:
            return _json.loads(self.content.decode("utf-8"))

    class _RequestsFallback:
        RequestException = Exception

        @staticmethod
        def get(url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: int = 8) -> _Resp:
            if params:
                url = f"{url}?{_urlparse.urlencode(params)}"
            req = _urlrequest.Request(url, headers=headers or {})
            with _urlrequest.urlopen(req, timeout=timeout) as handle:
                return _Resp(handle.read(), getattr(handle, "status", 200))

    requests = _RequestsFallback()

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None


class AssetManager:
    MIN_DIMENSIONS = {
        "plants": (640, 640),
        "backgrounds": (1280, 720),
        "decorations": (512, 512),
        "weather": (512, 512),
        "ui": (256, 256),
    }

    TARGET_ASPECTS = {
        "plants": 1.0,
        "backgrounds": 16 / 9,
        "decorations": 1.0,
        "weather": 16 / 9,
        "ui": 1.0,
    }

    QUALITY_THRESHOLDS = {
        "backgrounds": {"min_detail": 0.45, "max_compression": 0.45, "min_quality": 0.64},
        "plants": {"min_detail": 0.33, "max_compression": 0.58, "min_quality": 0.52},
        "decorations": {"min_detail": 0.30, "max_compression": 0.62, "min_quality": 0.48},
        "weather": {"min_detail": 0.28, "max_compression": 0.68, "min_quality": 0.45},
        "ui": {"min_detail": 0.25, "max_compression": 0.74, "min_quality": 0.4},
    }

    NO_KEY_PROVIDERS = {"wikimedia"}
    KEYED_PROVIDERS = {"unsplash", "pexels", "pixabay"}

    def __init__(self, config: Any, storage: Any) -> None:
        self.config = config
        self.storage = storage
        self.metadata = self.storage.load_asset_metadata()
        self.last_request_at = 0.0

    def get_or_fetch(
        self,
        category: str,
        key: str,
        query: str,
        provider_hint: Optional[str] = None,
        theme: Optional[str] = None,
        reroll: bool = False,
    ) -> Optional[Path]:
        cache_key = f"{category}:{key}"
        existing = self.metadata.get(cache_key, {})
        if not reroll:
            cached_path = existing.get("derivatives", {}).get("preview") or existing.get("local_path")
            if cached_path:
                p = self.storage.addon_dir / cached_path
                if p.exists():
                    return p

        providers = self._ordered_providers(provider_hint)
        best_pick: dict[str, Any] | None = None
        rejected: list[dict[str, Any]] = []

        for provider in providers:
            for candidate in self._fetch_candidates_from_provider(provider, query):
                scored = self.score_asset_candidate(candidate, category, theme=theme)
                if not scored.get("accepted"):
                    rejected.append(
                        {
                            "provider": provider,
                            "url": str(candidate.get("url", "")),
                            "reason": scored.get("reason", "rejected"),
                            "detail": scored.get("reason_detail", ""),
                        }
                    )
                    continue
                if not best_pick or scored["quality_score"] > best_pick["quality_score"]:
                    best_pick = scored

        if not best_pick:
            return self._fallback_curated_asset(category, key, query, theme=theme, rejected=rejected)

        downloaded = self._download(category, key, str(best_pick.get("url")))
        if not downloaded:
            return self._fallback_curated_asset(category, key, query, theme=theme, rejected=rejected)

        derivatives = self._generate_derivatives(downloaded, category, key)
        metadata_row = {
            "provider": best_pick.get("provider"),
            "query": query,
            "source_url": best_pick.get("url"),
            "source_kind": "remote",
            "attribution": best_pick.get("attribution", {}),
            "downloaded_at": int(time.time()),
            "local_path": str(downloaded.relative_to(self.storage.addon_dir)),
            "quality_score": round(float(best_pick.get("quality_score", 0.0)), 4),
            "dimensions": {
                "width": int(best_pick.get("width", 0)),
                "height": int(best_pick.get("height", 0)),
            },
            "style_tags": best_pick.get("style_tags", []),
            "theme_compatibility": round(float(best_pick.get("theme_compatibility", 0.0)), 4),
            "derivatives": {k: str(v.relative_to(self.storage.addon_dir)) for k, v in derivatives.items()},
            "rejection_log": rejected[:15],
        }
        self.metadata[cache_key] = metadata_row
        self.storage.save_asset_metadata(self.metadata)
        return derivatives.get("preview") or downloaded

    def score_asset_candidate(self, candidate: dict[str, Any], category: str, theme: Optional[str] = None) -> dict[str, Any]:
        width = int(candidate.get("width") or 0)
        height = int(candidate.get("height") or 0)
        if width <= 0 or height <= 0:
            width, height = self._probe_dimensions(str(candidate.get("url", "")))

        min_w, min_h = self.MIN_DIMENSIONS.get(category, (512, 512))
        if width < min_w or height < min_h:
            return {
                "accepted": False,
                "reason": "dimensions",
                "reason_detail": f"{width}x{height} < {min_w}x{min_h}",
                "width": width,
                "height": height,
            }

        threshold = self.QUALITY_THRESHOLDS.get(category, self.QUALITY_THRESHOLDS["decorations"])
        detail = float(candidate.get("detail_score", 0.65))
        compression = float(candidate.get("compression_penalty", 0.25))

        if detail < float(threshold["min_detail"]):
            return {
                "accepted": False,
                "reason": "detail",
                "reason_detail": f"detail_score {detail:.2f} below {threshold['min_detail']}",
                "width": width,
                "height": height,
            }

        if compression > float(threshold["max_compression"]):
            return {
                "accepted": False,
                "reason": "compression",
                "reason_detail": f"compression_penalty {compression:.2f} above {threshold['max_compression']}",
                "width": width,
                "height": height,
            }

        resolution_score = min(1.0, (width * height) / float(min_w * min_h * 4))
        aspect = width / max(1.0, height)
        target_aspect = self.TARGET_ASPECTS.get(category, 1.0)
        aspect_fit = max(0.0, 1.0 - min(1.0, abs(aspect - target_aspect)))
        theme_compat = self._theme_compatibility(candidate, theme)
        quality_score = (resolution_score * 0.4) + (aspect_fit * 0.3) + (theme_compat * 0.3)

        if quality_score < float(threshold["min_quality"]):
            return {
                "accepted": False,
                "reason": "quality",
                "reason_detail": f"quality_score {quality_score:.2f} below {threshold['min_quality']}",
                "width": width,
                "height": height,
                "quality_score": quality_score,
            }

        return {
            **candidate,
            "accepted": True,
            "width": width,
            "height": height,
            "aspect_fit": aspect_fit,
            "theme_compatibility": theme_compat,
            "quality_score": quality_score,
        }

    def _ordered_providers(self, provider_hint: Optional[str]) -> list[str]:
        configured = [str(p) for p in self.config.nested("image_api", "provider_priority", default=[]) or []]
        if provider_hint and provider_hint in configured:
            configured = [provider_hint] + [p for p in configured if p != provider_hint]

        no_key = [p for p in configured if p in self.NO_KEY_PROVIDERS]
        keyed = [p for p in configured if p in self.KEYED_PROVIDERS and self._provider_key_available(p)]
        return no_key + keyed

    def _provider_key_available(self, provider: str) -> bool:
        if provider == "unsplash":
            return bool(self.config.nested("image_api", "unsplash_access_key", default=""))
        if provider == "pexels":
            return bool(self.config.nested("image_api", "pexels_api_key", default=""))
        if provider == "pixabay":
            return bool(self.config.nested("image_api", "pixabay_api_key", default=""))
        return True

    def _fetch_candidates_from_provider(self, provider: str, query: str) -> list[dict[str, Any]]:
        attempts = min(2, int(self.config.nested("image_api", "max_retries", default=2) or 2))
        for _ in range(max(1, attempts)):
            self._wait_rate_limit()
            try:
                if provider == "wikimedia":
                    found = self._from_wikimedia(query)
                elif provider == "unsplash":
                    found = self._from_unsplash(query)
                elif provider == "pexels":
                    found = self._from_pexels(query)
                elif provider == "pixabay":
                    found = self._from_pixabay(query)
                else:
                    found = []
                if found:
                    return found
            except requests.RequestException:
                time.sleep(0.2)
        return []

    def _wait_rate_limit(self) -> None:
        min_gap = float(self.config.nested("image_api", "rate_limit_seconds", default=1.0))
        elapsed = time.time() - self.last_request_at
        if elapsed < min_gap:
            time.sleep(min_gap - elapsed)
        self.last_request_at = time.time()

    def _from_wikimedia(self, query: str) -> list[dict[str, Any]]:
        if not self.config.nested("image_api", "enable_builtin_no_key_sources", default=True):
            return []
        timeout = min(4, int(self.config.nested("image_api", "request_timeout_sec", default=8) or 8))
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,
                "gsrlimit": 10,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": 1600,
                "format": "json",
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        pages = (resp.json().get("query", {}).get("pages", {}) or {}).values()
        out: list[dict[str, Any]] = []
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            image_url = info.get("thumburl") or info.get("url")
            if not image_url:
                continue
            ext = info.get("extmetadata", {})
            out.append(
                {
                    "url": image_url,
                    "provider": "wikimedia",
                    "width": info.get("width"),
                    "height": info.get("height"),
                    "style_tags": ["encyclopedic", "natural"],
                    "attribution": {
                        "author": (ext.get("Artist", {}) or {}).get("value", ""),
                        "license": (ext.get("LicenseShortName", {}) or {}).get("value", ""),
                        "page_url": (ext.get("ImageDescription", {}) or {}).get("source", "")
                        or f"https://commons.wikimedia.org/wiki/{page.get('title', '')}",
                    },
                }
            )
        return out

    def _from_unsplash(self, query: str) -> list[dict[str, Any]]:
        key = self.config.nested("image_api", "unsplash_access_key", default="")
        if not key:
            return []
        timeout = min(4, int(self.config.nested("image_api", "request_timeout_sec", default=8) or 8))
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "orientation": "landscape", "per_page": 30},
            headers={"Authorization": f"Client-ID {key}"},
            timeout=timeout,
        )
        resp.raise_for_status()
        return [
            {
                "url": p["urls"]["regular"],
                "provider": "unsplash",
                "width": p.get("width"),
                "height": p.get("height"),
                "style_tags": ["photoreal", "modern"],
                "attribution": {
                    "author": p["user"]["name"],
                    "author_url": p["user"]["links"].get("html"),
                    "page_url": p["links"].get("html"),
                    "license": "Unsplash License",
                },
            }
            for p in resp.json().get("results", [])
        ]

    def _from_pexels(self, query: str) -> list[dict[str, Any]]:
        key = self.config.nested("image_api", "pexels_api_key", default="")
        if not key:
            return []
        timeout = min(4, int(self.config.nested("image_api", "request_timeout_sec", default=8) or 8))
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 30, "orientation": "landscape"},
            headers={"Authorization": key},
            timeout=timeout,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        return [
            {
                "url": p.get("src", {}).get("large") or p.get("src", {}).get("landscape"),
                "provider": "pexels",
                "width": p.get("width"),
                "height": p.get("height"),
                "style_tags": ["editorial", "outdoor"],
                "attribution": {
                    "author": p.get("photographer"),
                    "page_url": p.get("url"),
                    "license": "Pexels License",
                },
            }
            for p in photos
            if p.get("src")
        ]

    def _from_pixabay(self, query: str) -> list[dict[str, Any]]:
        key = self.config.nested("image_api", "pixabay_api_key", default="")
        if not key:
            return []
        timeout = min(4, int(self.config.nested("image_api", "request_timeout_sec", default=8) or 8))
        resp = requests.get(
            "https://pixabay.com/api/",
            params={"key": key, "q": query, "image_type": "photo", "per_page": 30, "safesearch": "true"},
            timeout=timeout,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        return [
            {
                "url": h.get("largeImageURL") or h.get("webformatURL"),
                "provider": "pixabay",
                "width": h.get("imageWidth"),
                "height": h.get("imageHeight"),
                "style_tags": ["stock"],
                "attribution": {
                    "author": h.get("user"),
                    "page_url": h.get("pageURL"),
                    "license": "Pixabay License",
                },
            }
            for h in hits
        ]

    def _download(self, category: str, key: str, url: str) -> Optional[Path]:
        if not url:
            return None
        timeout = min(4, int(self.config.nested("image_api", "request_timeout_sec", default=8) or 8))
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        ext = ".jpg"
        target = self.storage.assets_root / category / f"{key}_{digest}{ext}"
        if target.exists() and target.stat().st_size > 0:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(resp.content)
        return target

    def _generate_derivatives(self, original: Path, category: str, key: str) -> dict[str, Path]:
        cache_dir = self.storage.cache_dir / category
        cache_dir.mkdir(parents=True, exist_ok=True)
        derivatives = {
            "thumbnail": cache_dir / f"{key}_thumbnail.jpg",
            "preview": cache_dir / f"{key}_preview.jpg",
            "full": cache_dir / f"{key}_full.jpg",
        }
        if Image is None:
            for path in derivatives.values():
                path.write_bytes(original.read_bytes())
            return derivatives

        with Image.open(original) as img:
            for label, path in derivatives.items():
                clone = img.copy()
                if label == "thumbnail":
                    clone.thumbnail((256, 256))
                elif label == "preview":
                    clone.thumbnail((960, 960))
                else:
                    clone.thumbnail((2200, 2200))
                clone.save(path, format="JPEG", quality=90)
        return derivatives

    def _fallback_curated_asset(
        self,
        category: str,
        key: str,
        query: str,
        theme: Optional[str] = None,
        rejected: Optional[list[dict[str, Any]]] = None,
    ) -> Optional[Path]:
        curated_root = self.storage.assets_root / "starter_pack"
        curated_dir = curated_root / category
        matches = self._curated_matches(curated_dir, query=query, theme=theme)
        if not matches:
            any_assets = sorted(curated_root.glob("**/*.svg")) + sorted(curated_root.glob("**/*.jpg"))
            matches = [p for p in any_assets if p.is_file()]
        if not matches:
            matches = [self._ensure_placeholder_asset(curated_root)]

        picked = self._deterministic_pick(matches, f"{category}:{key}:{query}:{theme or ''}")
        cache_key = f"{category}:{key}"
        rel = str(picked.relative_to(self.storage.addon_dir))
        self.metadata[cache_key] = {
            "provider": "starter_pack",
            "query": query,
            "source_url": "local://starter_pack",
            "source_kind": "starter_pack",
            "attribution": {"author": "Anki Garden", "license": "CC0"},
            "downloaded_at": int(time.time()),
            "local_path": rel,
            "quality_score": 0.9,
            "dimensions": {"width": 0, "height": 0},
            "style_tags": ["starter_pack", "offline"],
            "theme_compatibility": 0.9,
            "rejection_log": (rejected or [])[:15],
            "derivatives": {"thumbnail": rel, "preview": rel, "full": rel},
        }
        self.storage.save_asset_metadata(self.metadata)
        return picked

    def _curated_matches(self, curated_dir: Path, query: str, theme: Optional[str]) -> list[Path]:
        if not curated_dir.exists():
            return []
        matches = sorted(curated_dir.glob("*.svg")) + sorted(curated_dir.glob("*.jpg"))
        if not matches:
            return []
        lowered_query = query.lower()
        lowered_theme = (theme or self.config.value("visual_theme", "verdant_dusk")).lower()
        preferred: list[Path] = []
        for candidate in matches:
            stem = candidate.stem.lower()
            if lowered_theme in stem:
                preferred.append(candidate)
                continue
            for term in lowered_query.split():
                if len(term) > 2 and term in stem:
                    preferred.append(candidate)
                    break
        return preferred or matches

    def _deterministic_pick(self, candidates: list[Path], seed: str) -> Path:
        if len(candidates) == 1:
            return candidates[0]
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % len(candidates)
        return candidates[idx]

    def _ensure_placeholder_asset(self, curated_root: Path) -> Path:
        placeholder = curated_root / "ui" / "fallback_placeholder.svg"
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        if not placeholder.exists():
            placeholder.write_text(
                """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 675'>\n"
                "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>\n"
                "<stop offset='0%' stop-color='#18252e'/><stop offset='100%' stop-color='#2f6f52'/></linearGradient></defs>\n"
                "<rect width='1200' height='675' fill='url(#g)'/>\n"
                "<text x='50%' y='52%' dominant-baseline='middle' text-anchor='middle' fill='#e6f0ea' font-size='46'>Anki Garden</text>\n"
                "</svg>\n""",
                encoding="utf-8",
            )
        return placeholder

    def _theme_compatibility(self, candidate: dict[str, Any], theme: Optional[str]) -> float:
        if not theme:
            theme = self.config.value("visual_theme", "verdant_dusk")
        tags = {str(t).lower() for t in candidate.get("style_tags", [])}
        score = 0.55
        if "natural" in tags or "photoreal" in tags:
            score += 0.1
        if theme in ("moonlit_study", "verdant_dusk") and "modern" in tags:
            score += 0.08
        if theme == "morning_bloom" and "outdoor" in tags:
            score += 0.12
        return min(1.0, score)

    def _probe_dimensions(self, url: str) -> tuple[int, int]:
        if not url:
            return (0, 0)
        timeout = min(4, int(self.config.nested("image_api", "request_timeout_sec", default=8) or 8))
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        content = resp.content
        if Image is not None:
            try:
                from io import BytesIO

                with Image.open(BytesIO(content)) as img:
                    return img.size
            except Exception:
                return (0, 0)
        return (0, 0)

    def export_metadata_json(self) -> str:
        return json.dumps(self.metadata, indent=2)
