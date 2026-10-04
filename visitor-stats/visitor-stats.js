(() => {
  'use strict';

  const panels = document.querySelectorAll('[data-visitor-host]');
  const preview = new URLSearchParams(window.location.search).get('visitor-preview') === '1';

  panels.forEach(panel => {
    if (panel.dataset.visitorInitialized === 'true') return;
    panel.dataset.visitorInitialized = 'true';
    const live = window.location.hostname === panel.dataset.visitorHost &&
      window.location.pathname.startsWith(panel.dataset.visitorPath);

    panel.querySelectorAll('[data-visitor-src]').forEach(image => {
      const status = image.closest('figure').querySelector('.hydra-visitors-status');

      // Ordinary local previews and offline archive use must not add visits.
      if (!live && !preview) {
        status.textContent = 'Open the live website to view visitor statistics.';
        return;
      }

      const slowLoad = window.setTimeout(() => {
        status.textContent = 'Statistics are taking longer to load. Open the full report below.';
      }, 15000);

      image.addEventListener('load', () => {
        window.clearTimeout(slowLoad);
        image.hidden = false;
        status.hidden = true;
      }, { once: true });

      image.addEventListener('error', () => {
        window.clearTimeout(slowLoad);
        image.hidden = true;
        status.hidden = false;
        status.textContent = 'Visitor statistics are temporarily unavailable. Open the full report below.';
      }, { once: true });

      // Both widgets use one counter. They load on page opening, even below the fold.
      image.src = image.dataset.visitorSrc;
    });
  });
})();
