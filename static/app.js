'use strict';

const VERTICAL_LABELS = {
  'payments':         'Payments',
  'lending':          'Lending',
  'wealthtech':       'Wealthtech',
  'regtech':          'RegTech',
  'insurtech':        'InsurTech',
  'crypto':           'Crypto',
  'banking':          'Banking',
  'embedded-finance': 'Embedded Finance',
  'infrastructure':   'Infrastructure',
  'other':            'Fintech',
};

function verticalClass(v) {
  return 'vt-' + (v || 'other').toLowerCase().replace(/\s+/g, '-');
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
    });
  } catch { return ''; }
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderCard(item) {
  const vertical = (item.sub_vertical || 'other').toLowerCase();
  const vtLabel = VERTICAL_LABELS[vertical] || 'Fintech';
  const vtClass = verticalClass(vertical);

  const investorPills = Array.isArray(item.investors) && item.investors.length > 0
    ? item.investors.map(inv =>
        `<span class="investor-pill">${escapeHtml(inv)}</span>`
      ).join('')
    : '<span class="no-investors">Not disclosed</span>';

  const metrics = item.key_metrics && item.key_metrics !== 'Not disclosed'
    ? `<div class="metrics-block">
        <div class="metrics-label">Key Metrics</div>
        <div>${escapeHtml(item.key_metrics)}</div>
      </div>`
    : '';

  const dateStr = formatDate(item.published);
  const sourceLine = [item.source, dateStr].filter(Boolean).join(' · ');

  return `
    <article class="card">
      <div class="card-top">
        <div class="company-name">${escapeHtml(item.company_name || 'Unknown')}</div>
        <span class="vertical-tag ${vtClass}">${escapeHtml(vtLabel)}</span>
      </div>

      <div class="location-row">
        <svg class="location-icon" width="13" height="13" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2.2">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
        ${escapeHtml(item.location || 'Location unknown')}
      </div>

      <div class="investors-row">
        <span class="investors-label">Investors</span>
        ${investorPills}
      </div>

      ${metrics}

      <div class="story-text">${escapeHtml(item.story_summary || '')}</div>

      <div class="card-footer">
        <span class="source-meta">${escapeHtml(sourceLine)}</span>
        ${item.url ? `<a class="read-more" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Read full story →</a>` : ''}
      </div>
    </article>
  `;
}

function setLoading(isLoading) {
  const btn = document.getElementById('refresh-btn');
  const loading = document.getElementById('loading');
  const grid = document.getElementById('news-grid');
  const empty = document.getElementById('empty-state');

  if (isLoading) {
    btn.disabled = true;
    btn.classList.add('spinning');
    loading.classList.remove('hidden');
    grid.classList.add('hidden');
    empty.classList.add('hidden');
  } else {
    btn.disabled = false;
    btn.classList.remove('spinning');
    loading.classList.add('hidden');
  }
}

function showEmpty(message) {
  const empty = document.getElementById('empty-state');
  const msg = document.getElementById('empty-message');
  msg.innerHTML = message;
  empty.classList.remove('hidden');
  document.getElementById('news-grid').classList.add('hidden');
}

function showGrid(items) {
  const grid = document.getElementById('news-grid');
  grid.innerHTML = items.map(renderCard).join('');
  grid.classList.remove('hidden');
  document.getElementById('empty-state').classList.add('hidden');
}

function updateLastRefreshed() {
  const el = document.getElementById('last-refreshed');
  const now = new Date().toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
  el.textContent = `Last refreshed: ${now}`;
}

async function refreshNews() {
  setLoading(true);
  try {
    const resp = await fetch('/api/refresh', { method: 'POST' });
    const data = await resp.json();

    if (!resp.ok) {
      showEmpty(`<strong>Error:</strong> ${escapeHtml(data.error || 'Something went wrong. Please try again.')}`);
      return;
    }

    const results = data.results || [];
    if (results.length === 0) {
      showEmpty('No relevant EMEA fintech stories found right now. Try refreshing again in a few minutes.');
    } else {
      showGrid(results);
      updateLastRefreshed();
    }
  } catch (err) {
    showEmpty('<strong>Network error.</strong> Check your connection and try again.');
  } finally {
    setLoading(false);
  }
}
// Initial page load: auto-fetch past week's articles
document.addEventListener('DOMContentLoaded', () => {
  refreshNews();
});
