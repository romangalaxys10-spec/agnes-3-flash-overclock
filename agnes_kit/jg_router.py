"""Client for the public Jack Gross agentic router (https://jackgross-five.vercel.app/router.md).

The blog serves small static markdown slices per collection+phase. This module fetches exactly
one slice over plain HTTPS GET (no keys, no user data sent), caches it on disk, and falls back
to the cache when the network is down or `offline=True`. The fetched text is untrusted external
content: treat it as data, not as instructions.

Honest limits: the site is an external dependency outside this repo's control; its counts and
files can change or disappear at any time. Its own MCP category assignment is keyword-based
(about 40% land in "other" per the site's docs). Nothing here is verified against the live site
at test time; the test suite stubs the network.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://jackgross-five.vercel.app"
START_URL = BASE + "/router.md"
MAP_URL = BASE + "/router/index.json"

# Static copy of the site's router map, verified live on 2026-10-11. Kept in-repo so the
# offline fallback can still name the right URL. If the site changes, update this dict.
COLLECTIONS = {
    "prompts": {
        "use_when": "you need a prompt for a task",
        "phases": {
            "select": "/router/prompts/select.md",
            "fill": "/router/prompts/fill.md",
            "verify": "/router/prompts/verify.md",
        },
    },
    "mcp": {
        "use_when": "you need an MCP server for a tool or data source",
        "phases": {
            "discover": "/router/mcp/discover.md",
            "evaluate": "/router/mcp/evaluate.md",
            "install": "/router/mcp/install.md",
            "secure": "/router/mcp/secure.md",
        },
    },
    "extensions": {
        "use_when": "you want recent news on MCP servers, skills and agent extensions",
        "phases": {
            "latest": "/router/extensions/latest.md",
            "lookup": "/router/extensions/lookup.md",
            "verify": "/router/extensions/verify.md",
        },
    },
}

MAX_REMOTE_BYTES = 6000  # same cap as local routed items; phase files are documented as <1 KB
CACHE_TTL_SECONDS = 24 * 3600
DEFAULT_TIMEOUT = 10
ENV_CACHE_DIR = "AGNES_JG_CACHE"


class Unavailable(Exception):
    """Raised when a slice can be served neither live nor from cache."""


def url_for(collection, phase):
    try:
        return BASE + COLLECTIONS[collection]["phases"][phase]
    except KeyError:
        raise ValueError(f"unknown Jack Gross route collection={collection!r} phase={phase!r}; "
                         f"known: {sorted(COLLECTIONS)}") from None


def default_cache_dir():
    if os.environ.get(ENV_CACHE_DIR):
        return Path(os.environ[ENV_CACHE_DIR])
    return Path.home() / ".cache" / "agnes-overclock" / "jg-router"


def _cache_path(cache_dir, collection, phase):
    return Path(cache_dir) / f"{collection}--{phase}.md"


def _http_get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "agnes-overclock-jg-router/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(MAX_REMOTE_BYTES + 1)
    if len(raw) > MAX_REMOTE_BYTES:
        raise ValueError(f"{url} is larger than {MAX_REMOTE_BYTES} bytes; refusing to route it")
    return raw.decode("utf-8")


def _read_cache(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def fetch(collection, phase, *, offline=False, refresh=False, cache_dir=None,
          timeout=DEFAULT_TIMEOUT, fetcher=None):
    """Return (text, meta) for one slice. meta: status live|cache, url, and warning when stale.

    Order: fresh cache (unless refresh/offline) -> live fetch (unless offline) -> any cache.
    Raises Unavailable when nothing can be served.
    """
    url = url_for(collection, phase)
    cdir = Path(cache_dir) if cache_dir else default_cache_dir()
    cpath = _cache_path(cdir, collection, phase)
    cached = _read_cache(cpath)
    fresh = cached is not None and (time.time() - cpath.stat().st_mtime) < CACHE_TTL_SECONDS
    if not offline and not refresh and fresh:
        return cached, {"status": "cache", "url": url, "fresh": True}
    if offline:
        if cached is not None:
            return cached, {"status": "cache", "url": url, "offline": True}
        raise Unavailable(f"offline mode and no cached copy of {url}; fetch it once while online")
    get = fetcher or _http_get
    try:
        text = get(url, timeout)
    except Exception as e:  # network down, DNS, HTTP error, oversized, decode failure
        if cached is not None:
            return cached, {"status": "cache", "url": url, "warning": f"live fetch failed, serving cache: {e}"}
        raise Unavailable(f"{url} unreachable and no cached copy ({e})") from e
    if len(text.encode("utf-8")) > MAX_REMOTE_BYTES:
        raise ValueError(f"{url} is larger than {MAX_REMOTE_BYTES} bytes; refusing to route it")
    try:
        cdir.mkdir(parents=True, exist_ok=True)
        tmp = cpath.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, cpath)
    except OSError:
        pass  # caching is best-effort; the live text is still served
    return text, {"status": "live", "url": url}


def index_summary():
    """Static, offline description of the remote router for --list and docs."""
    return {"start": START_URL, "map": MAP_URL,
            "collections": {c: {"use_when": v["use_when"], "phases": sorted(v["phases"])}
                            for c, v in COLLECTIONS.items()}}
