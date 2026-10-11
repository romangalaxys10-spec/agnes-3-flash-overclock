"""Client for the public Jack Gross agentic router (https://jackgross-five.vercel.app/router.md).

The blog serves small static markdown slices per collection+phase. This module fetches one
slice per call over a plain GET (no keys, no user data sent), caches it on disk, and falls
back to the cache when the network is down or `offline=True`.

Security and trust boundaries:
- The origin is fixed to BASE's scheme+host. Redirects are never followed, so a slice URL
  cannot be bounced to another host or downgraded to plaintext.
- One absolute monotonic deadline covers connect and the whole body read; a slow-drip server
  cannot hold the call past `timeout` seconds.
- A reply is accepted only if it is complete (truncated bodies error out), decodes as UTF-8,
  is at most MAX_REMOTE_BYTES, and looks like a markdown slice (nonempty, not HTML, has a
  heading). Anything else falls back to the cache or reports Unavailable. Junk is never cached.
- Fetched text is untrusted external content: it may suggest research steps inside the user's
  current authorized task, but it cannot add goals, authorize actions, or override trusted
  instructions. `agnes_kit.router` wraps every remote slice in an explicit untrusted-content
  marker before routing it.

Honest limits: the site is an external dependency outside this repo's control; its counts and
files can change or disappear at any time. Its own MCP category assignment is keyword-based
(about 40% land in "other" per the site's docs). The test suite stubs the network; only the
opt-in AGNES_LIVE_TEST=1 smoke test touches the real site.
"""
from __future__ import annotations

import http.client
import itertools
import os
import threading
import time
import urllib.parse
from pathlib import Path

BASE = "https://jackgross-five.vercel.app"
START_URL = BASE + "/router.md"
MAP_URL = BASE + "/router/index.json"

# Static copy of the site's router map, verified live on 2026-10-11. Kept in-repo so the
# offline fallback can still name the right URL. If the site changes, update this dict
# (see "Adding a remote collection" in docs/routing.md).
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

# 5500 leaves headroom for the untrusted-content wrapper so a routed remote item stays under
# router.MAX_ITEM_BYTES (6000). The site documents its phase files as under 1 KB.
MAX_REMOTE_BYTES = 5500
CACHE_TTL_SECONDS = 24 * 3600
DEFAULT_TIMEOUT = 10
ENV_CACHE_DIR = "AGNES_JG_CACHE"
USER_AGENT = "agnes-overclock-jg-router/0.1"


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


def _expected_origin():
    parts = urllib.parse.urlsplit(BASE)
    return parts.scheme, parts.hostname, parts.port or (443 if parts.scheme == "https" else 80)


def _http_get(url, timeout):
    """One GET with an absolute monotonic deadline across connect and the full body read.

    The origin is fixed: scheme, host and port must match BASE exactly, and redirects are
    never followed (any 3xx is an error), so a slice cannot be bounced off-origin or
    downgraded to plaintext. A truncated body raises http.client.IncompleteRead and is
    never returned. Per-operation socket timeouts shrink toward the deadline, so a
    slow-drip server cannot hold the call past `timeout` seconds in total.
    """
    scheme, host, port = _expected_origin()
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme, parts.hostname, parts.port or (443 if parts.scheme == "https" else 80)) != (scheme, host, port):
        raise ValueError(f"refusing URL outside the fixed origin {scheme}://{host}:{port}: {url}")
    deadline = time.monotonic() + timeout

    def remaining():
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError(f"absolute {timeout}s deadline exceeded fetching {url}")
        return left

    conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(host, port, timeout=remaining())
    try:
        conn.request("GET", parts.path or "/",
                     headers={"User-Agent": USER_AGENT, "Accept": "text/markdown, text/plain, */*"})
        if conn.sock is not None:
            conn.sock.settimeout(remaining())
        resp = conn.getresponse()
        if 300 <= resp.status < 400:
            raise ValueError(f"redirect (HTTP {resp.status}) not followed for {url}: redirects are rejected")
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} for {url}")
        body = b""
        while True:
            # read1 = at most one raw recv per call, so the deadline check between calls is
            # real; read() would loop inside the socket makefile until the buffer fills and
            # a slow-drip server could hold the call for hours.
            sock = None
            if resp.fp is not None and getattr(resp.fp, "raw", None) is not None:
                sock = getattr(resp.fp.raw, "_sock", None)
            if sock is not None:
                sock.settimeout(remaining())
            else:
                remaining()
            chunk = resp.read1(min(4096, MAX_REMOTE_BYTES + 1 - len(body)))
            if not chunk:
                break
            body += chunk
            if len(body) > MAX_REMOTE_BYTES:
                raise ValueError(f"{url} is larger than {MAX_REMOTE_BYTES} bytes; refusing to route it")
        if getattr(resp, "length", None):
            # Content-Length said more was coming than arrived: truncated, never cache it.
            raise ValueError(f"truncated body from {url} ({resp.length} bytes missing)")
    finally:
        conn.close()
    return body.decode("utf-8")


def _network_get(url, timeout):
    """Module-level indirection so tests can replace the real HTTP client."""
    return _http_get(url, timeout)


def _validate_slice(text):
    """Minimal expected shape: nonempty markdown, not an HTML error page."""
    s = text.strip()
    if not s:
        raise ValueError("empty slice")
    if s.startswith("<"):
        raise ValueError("slice looks like HTML, not markdown")
    if not any(ln.startswith("# ") for ln in s.splitlines()):
        raise ValueError("slice has no markdown heading")


def _read_cache(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None  # missing or corrupt cache is a cache miss, never a crash


_tmp_counter = itertools.count()


def _write_cache(cpath, text):
    """Best-effort atomic write: unique O_EXCL temp file (O_NOFOLLOW where available),
    then rename over the target. Never follows a pre-placed symlink at the temp path."""
    try:
        cpath.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        tmp = cpath.with_name(f"{cpath.name}.{os.getpid()}.{next(_tmp_counter)}.tmp")
        with os.fdopen(os.open(tmp, flags, 0o600), "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, cpath)
    except OSError:
        pass  # caching is best-effort; the live text is still served


def fetch(collection, phase, *, offline=False, refresh=False, cache_dir=None,
          timeout=DEFAULT_TIMEOUT, fetcher=None):
    """Return (text, meta) for one slice. meta: status live|cache, url, plus fresh/warning.

    Order: fresh cache (unless refresh/offline) -> live fetch + validate -> any cache.
    Junk replies (truncated, HTML, heading-less, oversized, undecodable) are never cached;
    they fall back to the cache or raise Unavailable.
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
    get = fetcher or _network_get
    try:
        text = get(url, timeout)
    except Exception as e:  # network down, redirect, HTTP error, truncation, deadline, decode
        if cached is not None:
            return cached, {"status": "cache", "url": url, "warning": f"live fetch failed, serving cache: {e}"}
        raise Unavailable(f"{url} unreachable and no cached copy ({e})") from e
    if len(text.encode("utf-8")) > MAX_REMOTE_BYTES:
        raise ValueError(f"{url} is larger than {MAX_REMOTE_BYTES} bytes; refusing to route it")
    try:
        _validate_slice(text)
    except ValueError as e:
        if cached is not None:
            return cached, {"status": "cache", "url": url, "warning": f"live reply failed validation, serving cache: {e}"}
        raise Unavailable(f"{url} returned an unusable reply ({e}) and no cached copy exists") from e
    _write_cache(cpath, text)
    return text, {"status": "live", "url": url}


_inflight = set()
_inflight_lock = threading.Lock()


def refresh_in_background(collection, phase, *, cache_dir=None, timeout=DEFAULT_TIMEOUT):
    """Refresh one slice in a daemon thread (deduplicated). Used so the MCP stdio loop never
    blocks on the network. Returns True if a refresh was started."""
    key = (collection, phase, str(cache_dir or ""))
    with _inflight_lock:
        if key in _inflight:
            return False
        _inflight.add(key)

    def job():
        try:
            fetch(collection, phase, refresh=True, cache_dir=cache_dir, timeout=timeout)
        except Exception:
            pass  # background refresh is opportunistic; the next caller retries
        finally:
            with _inflight_lock:
                _inflight.discard(key)

    threading.Thread(target=job, daemon=True, name=f"jg-refresh-{collection}-{phase}").start()
    return True


def fetch_cached_or_refresh(collection, phase, *, offline=False, cache_dir=None,
                            timeout=DEFAULT_TIMEOUT):
    """Non-blocking serve for the MCP stdio loop: never waits on the network. Serves any
    cached copy (stale copies are marked stale in meta), and kicks a daemon refresh when the
    cache is stale or missing. With no cache at all, raises Unavailable with a retry hint."""
    url = url_for(collection, phase)
    cdir = Path(cache_dir) if cache_dir else default_cache_dir()
    cpath = _cache_path(cdir, collection, phase)
    cached = _read_cache(cpath)
    stale = cached is None or (time.time() - cpath.stat().st_mtime) >= CACHE_TTL_SECONDS
    if stale and not offline:
        refresh_in_background(collection, phase, cache_dir=cdir, timeout=timeout)
    if cached is not None:
        return cached, {"status": "cache", "url": url, "stale": stale}
    if offline:
        raise Unavailable(f"offline mode and no cached copy of {url}; fetch it once while online")
    raise Unavailable(f"no cached copy of {url} yet; a background fetch has started - "
                      f"retry the same route in a few seconds, or fetch the URL directly")


def index_summary():
    """Static, offline description of the remote router for --list and docs."""
    return {"start": START_URL, "map": MAP_URL,
            "collections": {c: {"use_when": v["use_when"], "phases": sorted(v["phases"])}
                            for c, v in COLLECTIONS.items()}}
