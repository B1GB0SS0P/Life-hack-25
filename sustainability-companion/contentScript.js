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
(async function() {
  console.log('♻️ [Eco] Starting contentScript');

  // 1) Wait for the page’s main container (so we don’t fire too early)
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

  // 4) Show skeleton & grade placeholder
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
      const { carbonScore, materialScore, endOfLifeScore, source, fetchedAt } = resp.data;
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
  Object.assign(sk.style, {
    position: 'fixed', top: '80px', right: '20px',
    background: '#fff', padding: '8px',
    border: '1px solid #ccc', borderRadius: '6px',
    zIndex: 999999
  });
  document.body.appendChild(sk);
}
function removeSkeleton() {
  const sk = document.getElementById('eco-skel');
  if (sk) sk.remove();
}

// Grade pill overlay on image
function injectGradePill(text) {
  if (document.getElementById('eco-grade-pill')) return;
  const container = document.querySelector('#imgTagWrapperId') || document.body;
  const pill = document.createElement('div');
  pill.id = 'eco-grade-pill';
  pill.textContent = text;
  Object.assign(pill.style, {
    position: 'absolute',
    top: '8px', right: '8px',
    background: '#2a9d8f', color: '#fff',
    padding: '2px 6px', fontWeight: 'bold',
    borderRadius: '4px', zIndex: 999999
  });
  container.style.position = 'relative';
  container.appendChild(pill);
}
function updateGradePill(letter) {
  const pill = document.getElementById('eco-grade-pill');
  if (pill) pill.textContent = letter;
}

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
      <div class="gauges">
        ${['carbon','material','endOfLife'].map(key =>
          gaugeHTML(key, data[`${key}Score`], `${key}Score` === focus)
        ).join('')}
      </div>
      <small class="meta">
        Source: ${data.source} • Updated: ${new Date(data.fetchedAt).toLocaleDateString()}
      </small>
      <div>
        <label><input type="checkbox" id="compare-toggle"> Compare alternatives</label>
      </div>
      <div id="eco-alts"></div>
    </div>`;
  Object.assign(panel.style, {
    position: 'fixed', top: '120px', right: '20px',
    background: '#fff', padding: '12px', width: '260px',
    border: '1px solid #ccc', borderRadius: '6px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    fontFamily: 'sans-serif', zIndex: 999999
  });
  document.body.appendChild(panel);

  document.getElementById('eco-toggle').onclick = () => {
    const body = document.getElementById('eco-body');
    body.hidden = !body.hidden;
    document.getElementById('eco-toggle').textContent =
      (body.hidden ? 'Show' : 'Hide') + ' Eco-Scores ' + (body.hidden ? '▼' : '▲');
  };
}

function gaugeHTML(name, value, highlight) {
  const color = highlight ? '#2a9d8f' : '#264653';
  const r = 40, c = 2 * Math.PI * r, o = c * (1 - value/100);
  return `
    <div class="gauge ${highlight?'focus':''}" title="${name} : ${value}/100">
      <svg width="100" height="60">
        <circle cx="50" cy="50" r="${r}" stroke="#eee" stroke-width="10" fill="none"/>
        <circle cx="50" cy="50" r="${r}" stroke="${color}" stroke-width="10"
          fill="none" stroke-dasharray="${c}" stroke-dashoffset="${o}"
          transform="rotate(-90 50 50)"/>
      </svg>
      <div style="font-size:12px; text-align:center;">
        ${name.charAt(0).toUpperCase()+name.slice(1)}: ${value}
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
    wrap.innerHTML = `<div style="background:#ddd;height:12px;width:40px;margin:6px 0;"></div>`;
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
        <div><strong>${delta>=0?'-':''}${delta}%</strong> vs this</div>
        <button class="swap-btn" data-asin="${asin}">Swap</button>`;
      wrap.querySelector('.swap-btn').style.display = 'none';
    });
  }

  document.getElementById('compare-toggle').onchange = e => {
    document.querySelectorAll('.alt-item .swap-btn')
      .forEach(btn => { btn.style.display = e.target.checked ? 'inline-block' : 'none'; });
  };
}
