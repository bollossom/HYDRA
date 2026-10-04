# HYDRA project website and interactive training logs

**HYDRA: Representation Harmonized Tokenization for Multimodal Generation and Understanding**

- Project page: https://bollossom.github.io/HYDRA/
- Interactive training logs: https://bollossom.github.io/HYDRA/training-logs/
- Research code: https://github.com/Tencent-Hunyuan/HYdra

The training dashboard contains HYDRA-1.5B and HYDRA-7B across three stages: 12 loss series, 10,800 logged rows, and 322 original generated images. Curves support inspecting values, zooming, toggling models, and CSV export. Image panels support checkpoint and sample selection, matching-step comparison, and playback.

## Website files

The full static website is stored in `site-bundle-*.zip` packages, with individual files and bundle checksums listed in `site-manifest.json`. Packages keep the browser-uploaded repository manageable while retaining every source HTML, JSON, CSV, and original PNG file.

Run `python3 build_site.py` to verify checksums, restore the complete website in `_site/`, and install the visitor section on both pages. Then open `_site/index.html` in a browser, or serve `_site/` using any static web server. The training data, plots, and samples work offline; no external packages, API keys, W&B account, or CDN scripts are required for them.

GitHub Actions automatically restores and publishes `_site/` to GitHub Pages. To update the archived research content, replace the relevant bundles and regenerate `site-manifest.json` with the new SHA-256 values. The visitor section is maintained separately in `visitor-stats/` and applied by `visitor_stats.py` only after the original files pass checksum verification. Changes to that section do not require repacking the original bundles. `_site/` is generated output; run the build after editing the section, stylesheet, script, or configuration.

## Visitor map and country counts

The project page and training-log page share one real Flag Counter, `FeUW`, showing a visitor map and visitor counts by country. The public report is [HYDRA visitor statistics](https://info.flagcounter.com/FeUW). Flag Counter generally counts the same browser once in a 24-hour period; these are the service's visitor counts, not all-time unique people. Repeat visitors on later days can be counted again. The image displays are cached for approximately five minutes, so changes may take time to appear. Page-view totals are hidden because loading the two widgets can increase the service's page-view tally.

Visitor widgets depend on the optional external Flag Counter service. If it is unavailable or blocked, the section displays a fallback message and a link to the public report; the paper content and training archive remain usable. Automatic widget requests are limited to the configured production host and path. Local previews do not load the widgets by default, preserving the live counter during routine testing. To intentionally request the real widgets from a local preview, append `?visitor-preview=1` to the page URL; that preview may be counted by the service.

Loss export: 2026-09-28. Generated-image export: 2026-09-29. The source run mapping, selection notes, prompts, coverage, and per-image checksums are included in the training-log archive. Reconstruction images, unrelated experiments, console logs, and model weights are not part of this website.
