/**
 * home_autocomplete.js — autocompletado de nombres en el buscador.
 * Endpoint: GET /api/v1/public/certificates/autocomplete/?q=...
 * IDs en template: #cert-search-input  #cert-autocomplete-list
 */
(function () {
    'use strict';

    const input = document.getElementById('cert-search-input');
    const list = document.getElementById('cert-autocomplete-list');
    if (!input || !list) return;
    let timeout = null;

    function clear() {
        list.innerHTML = '';
        list.classList.add('hidden');
    }

    function htmlEscape(t) {
        return t.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    }

    function highlight(value, query) {
        if (!query) return htmlEscape(value);
        const tokens = query.trim().split(/\s+/).filter(Boolean);
        if (!tokens.length) return htmlEscape(value);
        const sorted = tokens
            .map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
            .sort((a, b) => b.length - a.length);
        const re = new RegExp('(' + sorted.join('|') + ')', 'gi');
        return htmlEscape(value).replace(re, '<mark class="bg-[#F58830]/25 text-[#F58830] px-0.5 rounded font-extrabold">$1</mark>');
    }

    function render(items, query) {
        if (!items || !items.length) return clear();
        list.classList.remove('hidden');
        list.innerHTML = items.map(item =>
            `<div class="flex items-center gap-2.5 px-3 py-3 cursor-pointer rounded-lg text-sm font-semibold text-[#162054] dark:text-white hover:bg-[#F58830]/10 transition-colors" data-value="${htmlEscape(item.name)}">
                <i class="fa-solid fa-user text-[#F58830] text-xs"></i>
                <span>${highlight(item.name, query)}</span>
            </div>`
        ).join('');

        Array.from(list.children).forEach(el => {
            el.addEventListener('click', () => {
                input.value = el.dataset.value;
                clear();
            });
        });
    }

    input.addEventListener('input', () => {
        const q = input.value.trim();
        clearTimeout(timeout);
        if (q.length < 2) return clear();
        timeout = setTimeout(() => {
            fetch('/api/v1/public/certificates/autocomplete/?q=' + encodeURIComponent(q))
                .then(r => r.json())
                .then(data => render((data.results || []).map(i => ({ name: i.name })), q))
                .catch(clear);
        }, 225);
    });

    document.addEventListener('click', e => {
        if (!input.contains(e.target) && !list.contains(e.target)) clear();
    });
})();
