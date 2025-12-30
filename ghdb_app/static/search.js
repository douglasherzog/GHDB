function ghdbOpenQuery(q) {
  const url = 'https://www.google.com/search?q=' + encodeURIComponent(q);
  window.open(url, '_blank', 'noopener');
}

function ghdbOpenTemplate(tpl, value) {
  const url =
    '/dorks/open?template=' +
    encodeURIComponent(tpl) +
    '&value=' +
    encodeURIComponent(value || '');
  window.open(url, '_blank', 'noopener');
}

document.addEventListener('click', (e) => {
  const el = e.target;
  if (!(el instanceof HTMLElement)) return;

  const action = el.dataset.action;
  if (!action) return;

  if (action === 'copy') {
    const t = el.dataset.text || '';
    navigator.clipboard.writeText(t);
    return;
  }

  if (action === 'open-query') {
    e.preventDefault();
    const q = el.dataset.query || '';
    ghdbOpenQuery(q);
    return;
  }

  if (action === 'open-template') {
    e.preventDefault();
    const tpl = el.dataset.template || '';
    const parent = el.closest('.result');
    const input = parent ? parent.querySelector('input[data-action="value"]') : null;
    const value = input && input instanceof HTMLInputElement ? input.value : '';
    ghdbOpenTemplate(tpl, value);
    return;
  }
});
