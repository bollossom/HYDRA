"""Install the shared visitor section after the archived website is verified."""

import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit


_CONFIG_KEYS = {"server", "counter_id", "statistics_url", "live_host", "live_path"}
_HEAD_START = "<!-- HYDRA visitor assets: start -->"
_HEAD_END = "<!-- HYDRA visitor assets: end -->"
_SECTION_START = "<!-- HYDRA visitor stats: start -->"
_SECTION_END = "<!-- HYDRA visitor stats: end -->"


def _load_config(path):
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read visitor configuration: {path}") from exc
    if not isinstance(config, dict) or set(config) != _CONFIG_KEYS:
        raise ValueError("Visitor configuration must contain exactly " + ", ".join(sorted(_CONFIG_KEYS)))
    if any(not isinstance(value, str) or not value for value in config.values()):
        raise ValueError("Visitor configuration values must be nonempty strings")
    if not re.fullmatch(r"[a-z0-9]+\.flagcounter\.com", config["server"]):
        raise ValueError("Visitor server must be a Flag Counter hostname")
    if not re.fullmatch(r"[A-Za-z0-9]{1,64}", config["counter_id"]):
        raise ValueError("Visitor counter_id must contain only letters and numbers")
    report = urlsplit(config["statistics_url"])
    if (
        report.scheme != "https"
        or report.netloc != "info.flagcounter.com"
        or report.path.rstrip("/") != "/" + config["counter_id"]
        or report.query
        or report.fragment
    ):
        raise ValueError("Visitor statistics_url must be the HTTPS report for the same counter_id")
    if not re.fullmatch(
        r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
        config["live_host"],
    ):
        raise ValueError("Visitor live_host must be a plain lowercase hostname")
    live_path = config["live_path"]
    if (
        not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*", live_path)
        or not live_path.endswith("/")
    ):
        raise ValueError("Visitor live_path must be an absolute directory path ending in /")
    return config


def _remove_overlay(document, start, end):
    if document.count(start) != document.count(end):
        raise ValueError("Incomplete visitor overlay markers in page")
    return re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", document, flags=re.S)


def _render_section(template, config, theme, container_class):
    base = "https://" + config["server"]
    counter = config["counter_id"]
    values = {
        "__CONTAINER_CLASS__": container_class,
        "__THEME__": theme,
        "__MAP_URL__": f"{base}/map/{counter}/size_l/txt_285E91/border_FFFFFF/pageviews_0/viewers_0/flags_1/",
        "__COUNTRIES_URL__": f"{base}/count2/{counter}/bg_FFFFFF/txt_285E91/border_FFFFFF/columns_2/maxflags_20/viewers_0/labels_1/pageviews_0/flags_1/percent_0/",
        "__STATS_URL__": config["statistics_url"],
        "__LIVE_HOST__": config["live_host"],
        "__LIVE_PATH__": config["live_path"],
    }
    rendered = template
    for placeholder, value in values.items():
        rendered = rendered.replace(placeholder, html.escape(value, quote=True))
    if re.search(r"__[A-Z_]+__", rendered):
        raise ValueError("Unknown placeholder in visitor section template")
    return f"{_SECTION_START}\n{rendered.strip()}\n{_SECTION_END}\n"


def install_visitor_stats(root, out):
    """Add one visitor section and its local assets to each verified page."""
    root, out = Path(root), Path(out)
    source = root / "visitor-stats"
    config = _load_config(source / "config.json")
    template = (source / "section.html").read_text(encoding="utf-8")
    assets = [source / "visitor-stats.css", source / "visitor-stats.js"]
    if any(not asset.is_file() for asset in assets):
        raise ValueError("Visitor stylesheet or script is missing")
    pages = [
        (out / "index.html", "assets/", "project", "container", "</main>"),
        (out / "training-logs/index.html", "../assets/", "archive", "hydra-visitors-inner", '<p class="bottom">'),
    ]
    prepared = []
    for path, prefix, theme, container_class, anchor in pages:
        document = path.read_text(encoding="utf-8")
        document = _remove_overlay(document, _HEAD_START, _HEAD_END)
        document = _remove_overlay(document, _SECTION_START, _SECTION_END)
        if document.count("</head>") != 1 or document.count(anchor) != 1:
            raise ValueError(f"Cannot find a unique visitor insertion location in {path}")
        section = _render_section(template, config, theme, container_class)
        head = (
            f"{_HEAD_START}\n"
            f'<link rel="stylesheet" href="{prefix}visitor-stats.css">\n'
            f'<script defer src="{prefix}visitor-stats.js"></script>\n'
            f"{_HEAD_END}\n"
        )
        document = document.replace("</head>", head + "</head>", 1)
        document = document.replace(anchor, section + anchor, 1)
        if theme == "archive":
            document = document.replace("Fully offline", "Offline training data")
        prepared.append((path, document))
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for asset in assets:
        shutil.copyfile(asset, out / "assets" / asset.name)
    for path, document in prepared:
        path.write_text(document, encoding="utf-8")
