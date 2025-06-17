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
; (async function () {
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
  const { preferredMetric = 'environmentalScore' } = await new Promise(res =>
    chrome.storage.sync.get({ preferredMetric: 'environmentalScore' }, res)
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
      const { environmentalScore, socialScore, governanceScore, recommendations } = resp.data;
      const avg = (environmentalScore + socialScore + governanceScore) / 3;

      renderDetailPanel(resp.data, preferredMetric, avg)
      findAndRenderAlternatives(recommendations, avg);
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

  const container = document.querySelector('#eco-detail') || document.body;

  const pill = document.createElement('div');
  pill.id = 'eco-grade-pill';
  pill.textContent = text;

  pill.style.position = 'absolute';  // position relative to container
  pill.style.top = '12px';
  pill.style.left = '160px';
  pill.style.textAlign = 'center';
  pill.style.justifyContent = 'center'
  pill.style.display = 'flex'
  pill.style.whiteSpace = 'nowrap'

  container.appendChild(pill);  // append only once here, inside eco-detail
}

function updateGradePill(letter) {
  const pill = document.getElementById('eco-grade-pill');
  const colorMap = {
    A: '#95d7ae',        // light green
    B: '#f9a825',        // light orange
    C: '#fff176',        // light yellow
    D: '#e53935',        // red
    F: '#000000',        // black
  };
  if (!pill) return;
  const trimmed = letter.trim();
  const lastChar = trimmed.slice(-1).toUpperCase();
  const colored = colorMap[lastChar];

  const baseText = trimmed.slice(0, -1);

  pill.innerHTML = `${baseText}&nbsp;<span style="color: ${colored}; font-size: 20px"> ${lastChar}</span>`;
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
function renderDetailPanel(data, focus, avg) {
  if (document.getElementById('eco-detail')) return;
  const panel = document.createElement('div');
  panel.id = 'eco-detail';
  panel.innerHTML = `
    <button id="eco-toggle">Show Eco-Scores ▼</button>
    <div id="eco-body" hidden>
      <div id="gauges" class="gauges">
        ${['environmental', 'social', 'governance'].map(key =>
    gaugeHTML(key, data[`${key}Score`], `${key}Score` === focus)
  ).join('')}
      </div>
      <small class="meta">
        Source: ${data.source} • Updated: ${new Date(data.fetchedAt).toLocaleDateString()}
      </small>

      <div id="eco-alts"></div>
    </div>`;
  `      <div>
        <label>
          <input type="checkbox" id="compare-toggle"> Compare alternatives
        </label>
      </div>`
  document.body.appendChild(panel);

  document.getElementById('eco-toggle').addEventListener('click', () => {
    const body = document.getElementById('eco-body');
    body.hidden = !body.hidden;
    document.getElementById('eco-toggle').textContent =
      (body.hidden ? 'Show' : 'Hide') + ' Eco-Scores ' + (body.hidden ? '▼' : '▲');
    if (!body.hidden) {
      animateGauges();
    }
    else {
      const fills = body.querySelectorAll('.gauge .fill');
      fills.forEach(circle => {
        const circumference = circle.getAttribute('stroke-dasharray');
        circle.style.strokeDashoffset = circumference;
      });
    }
  });

  injectInfoIcon('Environment', 'The scoring considers the impact the product has to the environment. Go to options for more info.')
  injectInfoIcon('Social', 'The scoring considers the social impact of the product such as welfare of workers. Go to options for more info.')
  injectInfoIcon('Governance', 'The scoring considers the impact the product has towards the Economy. Go to options for more info.')
  injectGradePill('…')
  updateGradePill(`Eco Score: ${computeGrade(avg)}`)

}

// Render individual gauge
function gaugeHTML(name, value, highlight) {
  const colorClass = highlight ? 'focus' : '';
  const r = 40;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - value / 100);
  return `
    <div class="graph">
      <div class="gauge ${colorClass}">
        <svg width="100" height="110">
          <circle cx="50" cy="50" r="${r}" stroke="#eee" stroke-width="10" fill="none"/>
          <circle cx="50" cy="50" r="${r}" stroke="${highlight ? '#32746d' : '#104f55'}" stroke-width="10" class="fill"
            fill="none"
            stroke-dasharray="${circumference}"
            stroke-dashoffset="${circumference}"
            data-offset="${offset}"
            transform="rotate(-90 50 50)"/>
          
          <text x="50" y="55" text-anchor="middle" dominant-baseline="middle" font-size="16" fill="#333">
            ${value}%
          </text>
        </svg>
        <div class="g-label">
          ${name.charAt(0).toUpperCase() + name.slice(1)} Score
        </div>
      </div>
    </div>`;
}

function animateGauges() {
  document.querySelectorAll('.gauge .fill').forEach(circle => {
    const offset = circle.getAttribute('data-offset');
    requestAnimationFrame(() => {
      circle.style.strokeDashoffset = offset;
    });
  });
}

// Inject info to the texts
function injectInfoIcon(labelText, tooltipText) {
  const labels = document.querySelectorAll('.graph');

  labels.forEach(label => {
    if (label.textContent.includes(labelText)) {
      // Prevent duplicates
      if (label.querySelector('.info-icon')) return;

      const icon = document.createElement('span');
      icon.className = 'info-icon';
      icon.textContent = '🛈';

      const tooltip = document.createElement('span');
      tooltip.className = 'tooltip-text';
      tooltip.textContent = tooltipText;

      icon.appendChild(tooltip);
      label.appendChild(icon);
    }
  });
}


// Alternatives section
async function findAndRenderAlternatives(mainData, avg) {
  console.log(avg)

  const container = document.getElementById('eco-alts');
  container.innerHTML = '<h5>Recommendations</h5>';

  for (let data of mainData) {
    const wrap = document.createElement('div');
    wrap.className = 'alt-item';

    const delta = Math.round(((data['product_score'] - avg) / avg) * 100);

    wrap.innerHTML = `
      <div class="summary-row">
        <div>${data['product_name']} is <strong>${Math.abs(delta)}% ${delta <= 0 ? 'less' : 'more'}</strong> Sustainable</div>
        <div class="button-wrap">
          <button class="swap-btn" style="margin: 5px 0;">View Reason</button>
          <div class="reason-text" style="display: none; margin-top: 5px; padding: 8px; background: #f9f9f9; border-left: 3px solid #32746d; color: #333;">
            ${data['reco_reason']}
          </div>
        </div>
      </div>
    `;

    container.appendChild(wrap);
  }


  container.addEventListener('click', e => {
    if (e.target.classList.contains('swap-btn')) {
      const reasonDiv = e.target.closest('.alt-item').querySelector('.reason-text');
      reasonDiv.style.display = reasonDiv.style.display === 'none' ? 'block' : 'none';
    }
  });
}
