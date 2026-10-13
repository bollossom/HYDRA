"""Restore the verified website, then install the visitor-statistics overlay."""
import hashlib
import json
import zipfile
from pathlib import Path

from visitor_stats import install_visitor_stats

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'site-manifest.json').read_text())
out = root / '_site'
out.mkdir(exist_ok=True)
for filename, expected in manifest['bundles'].items():
    archive = root / filename
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected, filename
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            target = (out / member.filename).resolve()
            assert target.is_relative_to(out.resolve()), member.filename
        z.extractall(out)
for filename, expected in manifest['files'].items():
    assert hashlib.sha256((out / filename).read_bytes()).hexdigest() == expected, filename
assert (out / 'index.html').exists()
assert (out / 'training-logs/index.html').exists()
assert len(list((out / 'training-logs/images').rglob('*.png'))) == 322
# Publish the model download link after verifying the archived website.
page = out / 'index.html'
html = page.read_text(encoding='utf-8')
placeholder = '<span class="pill pending" title="Model release is being prepared">🤗 &nbsp;Models · coming soon</span>'
models_link = '<a class="pill" href="https://huggingface.co/Xuerui123/HYdra" target="_blank" rel="noopener noreferrer">🤗 &nbsp;Models</a>'
assert html.count(placeholder) == 1, 'Expected one Models placeholder'
page.write_text(html.replace(placeholder, models_link), encoding='utf-8')

install_visitor_stats(root, out)
print(f"Verified {len(manifest['files'])} bundled files; restored both pages and installed visitor statistics.")
