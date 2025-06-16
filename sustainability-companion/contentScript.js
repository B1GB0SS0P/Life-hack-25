// contentScript.js

// Utility to wait for a selector to appear in the DOM
function waitForElement(selector, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const el = document.querySelector(selector);
    if (el) return resolve(el);

    const obs = new MutationObserver((_, observer) => {
      const found = document.querySelector(selector);
      if (found) {
        observer.disconnect();
        resolve(found);
      }
    });

    obs.observe(document.documentElement, { childList: true, subtree: true });
    setTimeout(() => {
      obs.disconnect();
      reject(new Error(`Timeout waiting for ${selector}`));
    }, timeout);
  });
}

// Entry point
;(async function() {
  console.log('♻️ [Eco] Starting contentScript');

  // 1) Wait for the <body> to exist
  try {
    await waitForElement('body');
    console.log('♻️ [Eco] Body is ready');
  } catch (err) {
    console.error('❌ [Eco] Body never appeared, aborting.', err);
    return;
  }

  // 2) Load user preference
  const { preferredMetric = 'carbonScore' } = await new Promise(res =>
    chrome.storage.sync.get({ preferredMetric: 'carbonScore' }, res)
  );
  console.log('♻️ [Eco] preferredMetric =', preferredMetric);

  // 3) Detect ASIN/UPC
  let upc = null;
  const meta = document.querySelector('meta[name="ASIN"]');
  if (meta) upc = meta.content;

  if (!upc) {
    const dataAsinEl = document.querySelector('[data-asin]:not([data-asin=""])');
    if (dataAsinEl) upc = dataAsinEl.getAttribute('data-asin');
  }

  if (!upc) {
    const m = window.location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/);
    if (m) upc = m[1];
  }

  console.log('🔍 [Eco] Detected ASIN/UPC =', upc);
  if (!upc) {
    console.warn('⚠️ [Eco] Could not find ASIN—giving up.');
    return;
  }

  // 4) Show skeleton & placeholder grade
  injectSkeleton();
  injectGradePill('…');

  // 5) Fetch the scores
  chrome.runtime.sendMessage(
    { action: 'fetchScore', upc },
    resp => {
      removeSkeleton();

      if (!resp?.success) {
        console.error('❌ [Eco] fetchScore failed:', resp?.error);
        return;
      }
      console.log('✅ [Eco] Score data:', resp.data);

      // 6) Compute grade & inject UI
      const { carbonScore, materialScore, endOfLifeScore } = resp.data;
      const avg = (carbonScore + materialScore + endOfLifeScore) / 3;
      updateGradePill(computeGrade(avg));

      renderDetailPanel(resp.data, preferredMetric);
      findAndRenderAlternatives(resp.data, preferredMetric);
    }
  );
})();


// ——— UI Helpers —————————————————————————————————————————

// Skeleton loader in top-right
function injectSkeleton() {
  if (document.getElementById('eco-skel')) return;
  const sk = document.createElement('div');
  sk.id = 'eco-skel';
  sk.innerHTML = `
    <div class="skel-panel">
      <div class="skel-line short"></div>
      <div class="skel-line med"></div>
      <div class="skel-line long"></div>
    </div>`;
  document.body.appendChild(sk);
}
function removeSkeleton() {
  document.getElementById('eco-skel')?.remove();
}

// Grade pill overlay on image
function injectGradePill(text) {
  if (document.getElementById('eco-grade-pill')) return;
  const container = document.querySelector('#imgTagWrapperId') || document.body;
  container.style.position = 'relative';
  const pill = document.createElement('div');
  pill.id = 'eco-grade-pill';
  pill.textContent = text;
  pill.style.top = '20px'
  pill.style.height = '24px';
  document.body.appendChild(pill);
  container.appendChild(pill);
}
function updateGradePill(letter) {
  const pill = document.getElementById('eco-grade-pill');
  if (pill) pill.textContent = letter;
}

// Compute A–F grade
function computeGrade(val) {
  if (val >= 80) return 'A';
  if (val >= 60) return 'B';
  if (val >= 40) return 'C';
  if (val >= 20) return 'D';
  return 'F';
}

// Main detail panel
function renderDetailPanel(data, focus) {
  if (document.getElementById('eco-detail')) return;
  const panel = document.createElement('div');
  panel.id = 'eco-detail';
  panel.innerHTML = `
    <button id="eco-toggle">Show Eco-Scores ▼</button>
    <div id="eco-body" hidden>
      <div id="gauges" class="gauges">
        ${['carbon','material','endOfLife'].map(key =>
          gaugeHTML(key, data[`${key}Score`], `${key}Score` === focus)
        ).join('')}
      </div>
      <small class="meta">
        Source: ${data.source} • Updated: ${new Date(data.fetchedAt).toLocaleDateString()}
      </small>
      <div>
        <label>
          <input type="checkbox" id="compare-toggle"> Compare alternatives
        </label>
      </div>
      <div id="eco-alts"></div>
    </div>`;
  document.body.appendChild(panel);

  document.getElementById('eco-toggle').addEventListener('click', () => {
    const body = document.getElementById('eco-body');
    body.hidden = !body.hidden;
    document.getElementById('eco-toggle').textContent =
      (body.hidden ? 'Show' : 'Hide') + ' Eco-Scores ' + (body.hidden ? '▼' : '▲');
  });
}

// Render individual gauge
function gaugeHTML(name, value, highlight) {
  const colorClass = highlight ? 'focus' : '';
  const r = 40;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - value/100);
  return `
    <div class="gauge ${colorClass}" title="${name} score: ${value}/100">
      <svg width="100" height="80">
        <circle cx="50" cy="50" r="${r}" stroke="#eee" stroke-width="10" fill="none"/>
        <circle cx="50" cy="50" r="${r}" stroke="${highlight ? '#2a9d8f' : '#264653'}" stroke-width="10"
          fill="none"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${offset}"
          transform="rotate(-90 50 50)"/>
      </svg>
      <div class="g-label">
        ${name.charAt(0).toUpperCase() + name.slice(1)}: ${value}
      </div>
    </div>`;
}

// Alternatives section
async function findAndRenderAlternatives(mainData, focus) {
  const altAsins = [...new Set(
    Array.from(document.querySelectorAll('[data-asin]'))
      .map(el => el.getAttribute('data-asin'))
      .filter(a => a && a !== mainData.upc)
  )].slice(0,3);

  const container = document.getElementById('eco-alts');
  container.innerHTML = '<h5>Alternatives</h5>';

  for (let asin of altAsins) {
    const wrap = document.createElement('div');
    wrap.className = 'alt-skel';
    wrap.innerHTML = `<div class="skel-line short"></div>`;
    container.appendChild(wrap);

    chrome.runtime.sendMessage({ action: 'fetchScore', upc: asin }, resp => {
      if (!resp.success) {
        wrap.textContent = 'Error loading alt';
        return;
      }
      const d = resp.data;
      const delta = Math.round(((mainData[focus] - d[focus]) / mainData[focus]) * 100);
      wrap.className = 'alt-item';
      wrap.innerHTML = `
        <div><strong>${delta >= 0 ? '-' : ''}${delta}%</strong> vs this</div>
        <button class="swap-btn" data-asin="${asin}">Swap</button>`;
      wrap.querySelector('.swap-btn').style.display = 'none';
    });
  }

  document.getElementById('compare-toggle').addEventListener('change', e => {
    document.querySelectorAll('.alt-item .swap-btn')
      .forEach(btn => {
        btn.style.display = e.target.checked ? 'inline-block' : 'none';
      });
  });
}
