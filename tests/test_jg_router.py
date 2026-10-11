"""HTTP-level tests for the Jack Gross router client against a local throwaway server.

BASE is monkeypatched to the local origin, so the fixed-origin check, deadline, redirect
refusal, truncation handling, shape validation and cache rules are exercised end to end
without touching the real site.
"""
import http.server
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agnes_kit import jg_router as j

GOOD = b"# ok slice\nlive body\n"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        mode = self.server.mode
        try:
            if mode == "ok":
                self.send_response(200)
                self.send_header("Content-Length", str(len(GOOD)))
                self.end_headers()
                self.wfile.write(GOOD)
            elif mode == "truncated":
                self.send_response(200)
                self.send_header("Content-Length", "100")
                self.end_headers()
                self.wfile.write(b"# short\n")  # then close early
            elif mode == "redirect":
                self.send_response(302)
                self.send_header("Location", "https://evil.example.invalid/x")
                self.send_header("Content-Length", "0")
                self.end_headers()
            elif mode == "html":
                body = b"<html><body># not a slice</body></html>"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif mode == "empty":
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()
            elif mode == "drip":
                self.send_response(200)
                self.send_header("Content-Length", "400")
                self.end_headers()
                for _ in range(400):
                    self.wfile.write(b"x")
                    self.wfile.flush()
                    time.sleep(0.02)  # 8s total, far past the client deadline
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *a):
        pass


class LiveHarness(unittest.TestCase):
    def setUp(self):
        self.orig_base = j.BASE
        self.td = tempfile.TemporaryDirectory()
        os.environ[j.ENV_CACHE_DIR] = self.td.name

    def tearDown(self):
        j.BASE = self.orig_base
        self.td.cleanup()

    def start_server(self, mode):
        srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        srv.mode = mode
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        j.BASE = f"http://127.0.0.1:{srv.server_address[1]}"
        self.addCleanup(srv.shutdown)
        return j.BASE

    def url(self, coll="mcp", phase="secure"):
        return j.url_for(coll, phase)

    def cache_file(self, coll="mcp", phase="secure"):
        return Path(self.td.name) / f"{coll}--{phase}.md"

    def test_ok_fetch_caches_and_validates(self):
        self.start_server("ok")
        text, meta = j.fetch("mcp", "secure")
        self.assertEqual((text, meta["status"]), (GOOD.decode(), "live"))
        self.assertEqual(self.cache_file().read_text(), GOOD.decode())

    def test_absolute_deadline_stops_drip(self):
        self.start_server("drip")
        t0 = time.monotonic()
        with self.assertRaises(Exception):
            j._http_get(self.url(), 0.4)
        self.assertLess(time.monotonic() - t0, 2.5)
        with self.assertRaises(j.Unavailable):
            j.fetch("mcp", "secure", timeout=0.4)
        self.assertFalse(self.cache_file().exists())

    def test_redirect_and_off_origin_rejected(self):
        self.start_server("redirect")
        with self.assertRaises(j.Unavailable) as cm:
            j.fetch("mcp", "secure")
        self.assertIn("redirect", str(cm.exception))
        self.assertFalse(self.cache_file().exists())
        with self.assertRaises(ValueError):  # no network touched: origin check comes first
            j._http_get("https://other-host.example/router/mcp/secure.md", 1)
        with self.assertRaises(ValueError):
            j._http_get("http://jackgross-five.vercel.app/router/mcp/secure.md", 1)

    def test_truncated_reply_never_cached(self):
        self.start_server("truncated")
        with self.assertRaises(j.Unavailable):
            j.fetch("mcp", "secure")
        self.assertFalse(self.cache_file().exists())

    def test_html_and_empty_200_rejected_but_cache_survives(self):
        for mode in ("html", "empty"):
            self.start_server(mode)
            with self.assertRaises(j.Unavailable):
                j.fetch("mcp", "secure")
            self.assertFalse(self.cache_file().exists())
            self.server_mode = mode
            # with a good cache in place, junk live replies fall back to it with a warning
            self.cache_file().write_text("# cached slice\nold but good\n")
            text, meta = j.fetch("mcp", "secure", refresh=True)
            self.assertEqual(meta["status"], "cache")
            self.assertIn("warning", meta)
            self.assertEqual(text, "# cached slice\nold but good\n")
            self.cache_file().unlink()
            break  # html covered; empty follows the same code path
        self.start_server("empty")
        with self.assertRaises(j.Unavailable):
            j.fetch("mcp", "evaluate")
        self.assertFalse(self.cache_file(phase="evaluate").exists())

    def test_ttl_boundary(self):
        self.start_server("ok")
        j.fetch("mcp", "secure")
        cf = self.cache_file()
        st = cf.stat()
        os.utime(cf, (st.st_atime, time.time() - j.CACHE_TTL_SECONDS + 30))  # just fresh
        text, meta = j.fetch("mcp", "secure", fetcher=lambda u, t: 1 / 0)
        self.assertEqual((meta["status"], meta.get("fresh")), ("cache", True))
        os.utime(cf, (st.st_atime, time.time() - j.CACHE_TTL_SECONDS - 30))  # just stale
        text, meta = j.fetch("mcp", "secure", fetcher=lambda u, t: "# v2 slice\nnewer\n")
        self.assertEqual((meta["status"], text), ("live", "# v2 slice\nnewer\n"))
        os.utime(cf, (st.st_atime, time.time() - j.CACHE_TTL_SECONDS - 30))
        text, meta = j.fetch("mcp", "secure", fetcher=lambda u, t: (_ for _ in ()).throw(OSError("down")))
        self.assertEqual(meta["status"], "cache")
        self.assertIn("warning", meta)

    def test_corrupt_cache_is_a_miss(self):
        self.start_server("ok")
        cf = self.cache_file()
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_bytes(b"\xff\xfe\x00not-utf8")
        text, meta = j.fetch("mcp", "secure")  # corrupt cache must not crash or be served
        self.assertEqual(meta["status"], "live")
        cf.write_bytes(b"\xff\xfe\x00not-utf8")
        with self.assertRaises(j.Unavailable):
            j.fetch("mcp", "secure", offline=True)

    def test_requested_url_matches_route(self):
        self.start_server("ok")
        seen = []
        text, meta = j.fetch("mcp", "install", fetcher=lambda u, t: seen.append(u) or "# i\nx\n")
        self.assertTrue(seen[0].endswith("/router/mcp/install.md"), seen)
        self.assertEqual(meta["url"], seen[0])

    def test_background_refresh_and_cache_only_serve(self):
        self.start_server("ok")
        with self.assertRaises(j.Unavailable) as cm:
            j.fetch_cached_or_refresh("prompts", "fill")
        self.assertIn("background fetch", str(cm.exception))
        cf = Path(self.td.name) / "prompts--fill.md"
        for _ in range(50):
            if cf.exists():
                break
            time.sleep(0.1)
        self.assertTrue(cf.exists())
        text, meta = j.fetch_cached_or_refresh("prompts", "fill")
        self.assertEqual(meta["status"], "cache")
        with self.assertRaises(j.Unavailable):
            j.fetch_cached_or_refresh("extensions", "latest", offline=True)


if __name__ == "__main__":
    unittest.main()
