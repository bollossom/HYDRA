"""Tests for visitor integration without contacting the statistics service."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from visitor_stats import install_visitor_stats


CONFIG = {
    "server": "s01.flagcounter.com",
    "counter_id": "FeUW",
    "statistics_url": "https://info.flagcounter.com/FeUW",
    "live_host": "bollossom.github.io",
    "live_path": "/HYDRA/",
}
TEMPLATE = '''<section id="hydra-visitors" data-theme="__THEME__" data-live-host="__LIVE_HOST__" data-live-path="__LIVE_PATH__"><div class="__CONTAINER_CLASS__"><a href="__STATS_URL__"><img data-src="__MAP_URL__" alt="Visitor map"><img data-src="__COUNTRIES_URL__" alt="Countries"></a></div></section>'''
PROJECT = "<!doctype html><html><head><title>HYDRA</title></head><body><main><section>Research</section></main></body></html>"
ARCHIVE = '<!doctype html><html><head><title>Archive</title></head><body><main><div id="stages"></div><p class="bottom">Fully offline</p></main></body></html>'


class VisitorStatsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "_site"
        self.source = self.root / "visitor-stats"
        self.source.mkdir()
        (self.source / "config.json").write_text(json.dumps(CONFIG))
        (self.source / "section.html").write_text(TEMPLATE)
        (self.source / "visitor-stats.css").write_text(".hydra-visitors { color: #285e91; }")
        (self.source / "visitor-stats.js").write_text("/* No network requests in tests. */")
        self.restore_pages()

    def restore_pages(self):
        (self.out / "training-logs").mkdir(parents=True, exist_ok=True)
        (self.out / "index.html").write_text(PROJECT)
        (self.out / "training-logs/index.html").write_text(ARCHIVE)

    def assert_valid_output(self):
        for relative, prefix, theme, container in [
            ("index.html", "assets/", "project", "container"),
            ("training-logs/index.html", "../assets/", "archive", "hydra-visitors-inner"),
        ]:
            page = (self.out / relative).read_text()
            self.assertEqual(page.count('id="hydra-visitors"'), 1)
            self.assertEqual(page.count(f'href="{prefix}visitor-stats.css"'), 1)
            self.assertEqual(page.count(f'<script defer src="{prefix}visitor-stats.js"></script>'), 1)
            self.assertIn(f'data-theme="{theme}"', page)
            self.assertIn(f'class="{container}"', page)
            self.assertIn('data-live-host="bollossom.github.io"', page)
            self.assertIn('data-live-path="/HYDRA/"', page)
            self.assertIn('href="https://info.flagcounter.com/FeUW"', page)
            self.assertIn("https://s01.flagcounter.com/map/FeUW/size_l/txt_285E91/border_FFFFFF/pageviews_0/viewers_0/flags_1/", page)
            self.assertIn("https://s01.flagcounter.com/count2/FeUW/bg_FFFFFF/txt_285E91/border_FFFFFF/columns_2/maxflags_20/viewers_0/labels_1/pageviews_0/flags_1/percent_0/", page)
            self.assertNotIn("__MAP_URL__", page)
            self.assertLess(page.index('id="hydra-visitors"'), page.index("</main>"))
            self.assertLess(page.index(f'href="{prefix}visitor-stats.css"'), page.index("</head>"))
            if theme == "archive":
                self.assertLess(page.index('id="hydra-visitors"'), page.index('<p class="bottom">'))
                self.assertIn("Offline training data", page)
                self.assertNotIn("Fully offline", page)
        for name in ("visitor-stats.css", "visitor-stats.js"):
            self.assertEqual((self.source / name).read_bytes(), (self.out / "assets" / name).read_bytes())

    def test_relative_links_and_single_insertion(self):
        install_visitor_stats(self.root, self.out)
        self.assert_valid_output()
        initial = [(self.out / name).read_text() for name in ("index.html", "training-logs/index.html")]
        install_visitor_stats(self.root, self.out)
        self.assert_valid_output()
        self.assertEqual(initial, [(self.out / name).read_text() for name in ("index.html", "training-logs/index.html")])

    def test_malformed_config_is_rejected_before_pages_change(self):
        bad_configs = [
            "not JSON", [], {"server": "s01.flagcounter.com"},
            dict(CONFIG, counter_id="FeUW/<script>"),
            dict(CONFIG, server="evil.example"),
            dict(CONFIG, statistics_url="http://info.flagcounter.com/FeUW"),
            dict(CONFIG, statistics_url="https://info.flagcounter.com/Other"),
            dict(CONFIG, live_host="https://bollossom.github.io"),
            dict(CONFIG, live_path="/HYDRA/../"),
            dict(CONFIG, live_path="/HYDRA/?preview=1"),
            dict(CONFIG, live_path=True),
        ]
        for config in bad_configs:
            with self.subTest(config=config):
                content = config if isinstance(config, str) else json.dumps(config)
                (self.source / "config.json").write_text(content)
                with self.assertRaises(ValueError):
                    install_visitor_stats(self.root, self.out)
                self.assertEqual((self.out / "index.html").read_text(), PROJECT)
                self.assertEqual((self.out / "training-logs/index.html").read_text(), ARCHIVE)
                self.assertFalse((self.out / "assets").exists())

    def test_repeated_complete_build_restores_archive_before_overlay(self):
        repository = Path(__file__).resolve().parents[1]
        for name in ("build_site.py", "visitor_stats.py"):
            (self.root / name).write_bytes((repository / name).read_bytes())
        files = {"index.html": PROJECT.encode(), "training-logs/index.html": ARCHIVE.encode()}
        for i in range(322):
            files[f"training-logs/images/sample_{i}.png"] = b"fixture image"
        bundle = self.root / "site-bundle-01.zip"
        with zipfile.ZipFile(bundle, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        manifest = {
            "bundles": {bundle.name: hashlib.sha256(bundle.read_bytes()).hexdigest()},
            "files": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        }
        (self.root / "site-manifest.json").write_text(json.dumps(manifest))
        original_bundle = bundle.read_bytes()
        original_manifest = (self.root / "site-manifest.json").read_bytes()
        for _ in range(2):
            completed = subprocess.run([sys.executable, str(self.root / "build_site.py")], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_valid_output()
            self.assertEqual(bundle.read_bytes(), original_bundle)
            self.assertEqual((self.root / "site-manifest.json").read_bytes(), original_manifest)


if __name__ == "__main__":
    unittest.main()
