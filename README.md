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

## Total page views

The project page and training-log page share the existing Flag Counter, `FeUW`, in one compact **Total page views** card. Its mini widget displays the shared page-view tally and provider logo, with country flags disabled. These are page views, not unique visitors. The public report is [HYDRA page-view statistics](https://info.flagcounter.com/FeUW).

The counter retains its full history, including the earlier period when both the map and country widgets loaded on each page opening. Those two requests could increase the provider's page-view tally, so the historical total includes the old dual-widget loads. The current section requests one mini widget per page opening; it does not reset or adjust the historical tally.

The widget depends on the optional external Flag Counter service. If it is unavailable or blocked, the card displays a fallback message and a link to the public report; the paper content and training archive remain usable. Automatic widget requests are limited to the configured production host and path. Local previews do not load the widget by default, preserving the live counter during routine testing. To intentionally request the real widget from a local preview, append `?visitor-preview=1` to the page URL; that preview may be counted by the service. Provider caching can delay visible updates.

Loss export: 2026-09-28. Generated-image export: 2026-09-29. The source run mapping, selection notes, prompts, coverage, and per-image checksums are included in the training-log archive. Reconstruction images, unrelated experiments, console logs, and model weights are not part of this website.
