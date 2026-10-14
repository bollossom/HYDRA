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

# Add paper access and citation after restoring and verifying the archived site.
html = page.read_text(encoding='utf-8')
code_link = '<a class="pill" href="https://github.com/Tencent-Hunyuan/HYdra" target="_blank" rel="noopener">⌘ &nbsp;Code</a>'
paper_link = '<a class="pill" href="https://arxiv.org/abs/2603.15228" target="_blank" rel="noopener noreferrer">📄 &nbsp;Paper</a>'
assert html.count(code_link) == 1, 'Expected one Code button'
assert html.count('</main>') == 1, 'Expected one homepage main element'
assert 'id="citation"' not in html, 'Citation already present in archive'
citation_styles = "\n    #citation { scroll-margin-top:70px; }\n    #citation .citation-meta { margin:0 auto 12px; color:var(--muted); font-size:15px; text-align:center; }\n    #citation pre { max-width:1000px; margin:22px auto 0; padding:22px; border:1px solid var(--line); border-radius:8px; background:var(--pale-2); white-space:pre-wrap; overflow-wrap:anywhere; }\n    #citation code { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:13px; line-height:1.7; }\n"
citation_section = "\n<section id=\"citation\" aria-labelledby=\"citation-title\">\n  <div class=\"container\">\n    <h2 class=\"section-title\" id=\"citation-title\">Citation</h2>\n    <p class=\"citation-meta\">Read the paper: <a href=\"https://arxiv.org/abs/2603.15228\" target=\"_blank\" rel=\"noopener noreferrer\">arXiv:2603.15228</a></p>\n    <p class=\"citation-meta\">Please cite HYDRA using the following BibTeX entry.</p>\n    <pre><code>@article{qiu2026hydra,\n  title={{HYDRA}: Representation Harmonized Tokenization for Multimodal Generation and Understanding},\n  author={Qiu, Xuerui and Cui, Yutao and Zhang, Guozhen and Li, Junzhe and Zhao, Yaqi and Zhang, Xiao and Li, Yang and Liu, Songtao and Yang, Miles and Shi, Yu and Zhong, Zhao and Bo, Liefeng},\n  journal={arXiv preprint arXiv:2603.15228},\n  year={2026}\n}</code></pre>\n  </div>\n</section>\n"
html = html.replace(code_link, paper_link + '\n        ' + code_link, 1)
html = html.replace('</style>', citation_styles + '\n</style>', 1)
html = html.replace('</main>', citation_section + '\n</main>', 1)

# Highlight the conference acceptance below the project title.
conference_title = "<h1>HYDRA: Representation Harmonized Tokenization<br>for Multimodal Generation and Understanding</h1>"
conference_badge = "<div class=\"conference-tag\"><span>NeurIPS 2026</span></div>"
conference_styles = "\n    .conference-tag { margin:18px auto 0; }\n    .conference-tag span { display:inline-block; padding:6px 16px; border:1px solid #bdd3e7; border-radius:999px; color:var(--blue-deep); background:var(--pale); font-size:15px; font-weight:750; letter-spacing:.02em; }\n"
assert html.count(conference_title) == 1, "Expected one project title"
assert html.count("</style>") == 1, "Expected one homepage style block"
assert 'class="conference-tag"' not in html, "Conference tag already present"
html = html.replace(conference_title, conference_title + "\n      " + conference_badge, 1)
html = html.replace("</style>", conference_styles + "\n</style>", 1)
page.write_text(html, encoding='utf-8')
print(f"Verified {len(manifest['files'])} bundled files; restored both pages and installed visitor statistics.")
