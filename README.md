# HYDRA project website and interactive training logs

**HYDRA: Representation Harmonized Tokenization for Multimodal Generation and Understanding**

- Project page: https://bollossom.github.io/HYDRA/
- Interactive training logs: https://bollossom.github.io/HYDRA/training-logs/
- Research code: https://github.com/Tencent-Hunyuan/HYdra

The training dashboard contains HYDRA-1.5B and HYDRA-7B across three stages: 12 loss series, 10,800 logged rows, and 322 original generated images. Curves support inspecting values, zooming, toggling models, and CSV export. Image panels support checkpoint and sample selection, matching-step comparison, and playback.

## Website files

The full static website is stored in `site-bundle-*.zip` packages, with individual files and bundle checksums listed in `site-manifest.json`. Packages keep the browser-uploaded repository manageable while retaining every source HTML, JSON, CSV, and original PNG file.

Run `python3 build_site.py` to verify checksums and restore the complete website in `_site/`. Then open `_site/index.html` in a browser, or serve `_site/` using any static web server. No external packages, API keys, W&B account, or CDN scripts are required.

GitHub Actions automatically restores and publishes `_site/` to GitHub Pages. To update the website, replace the relevant bundles and regenerate `site-manifest.json` with the new SHA-256 values, then commit the changes.

Loss export: 2026-09-28. Generated-image export: 2026-09-29. The source run mapping, selection notes, prompts, coverage, and per-image checksums are included in the training-log archive. Reconstruction images, unrelated experiments, console logs, and model weights are not part of this website.
