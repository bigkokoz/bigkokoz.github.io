(function () {
  'use strict';
  // Lee data/projects.json y arma la portada. No hay que tocar HTML para agregar proyectos.
  var COLORS = ['#ff7a1a', '#4a5cff', '#22c1a4', '#ff5c8a', '#9b59b6', '#f5a623'];
  var $ = function (id) { return document.getElementById(id); };

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function initials(t) { var w = (t || '?').trim().split(/\s+/); return (w.length > 1 ? w[0][0] + w[1][0] : w[0].slice(0, 2)).toUpperCase(); }
  function colorFor(id) { var h = 0; for (var i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0; return COLORS[h % COLORS.length]; }

  function media(p) {
    var wrap = el('div', 'media');
    var fb = function () { var f = el('div', 'fallback', initials(p.title)); f.style.background = colorFor(p.id); return f; };
    if (!p.thumb) { wrap.appendChild(fb()); return wrap; }
    var img = new Image(); img.src = p.thumb; img.alt = p.title; img.loading = 'lazy';
    img.onerror = function () { img.replaceWith(fb()); };
    wrap.appendChild(img); return wrap;
  }

  function buttons(p, big) {
    var row = el('div', 'btn-row');
    if (p.page) { var a = el('a', 'btn' + (big ? ' primary' : ' small primary'), 'Ver proyecto'); a.href = p.page; row.appendChild(a); }
    if (p.app) { var b = el('a', 'btn' + (big ? '' : ' small'), 'Abrir app'); b.href = p.app; if (/^https?:/.test(p.app)) { b.target = '_blank'; b.rel = 'noopener'; } row.appendChild(b); }
    if (!p.page && !p.app) { var c = el('button', 'btn small', 'Ver detalle'); c.type = 'button'; c.onclick = function () { openDetail(p); }; row.appendChild(c); }
    return row;
  }

  function chips(p) { var c = el('div', 'chips'); (p.tags || []).forEach(function (t) { c.appendChild(el('span', 'chip', t)); }); return c; }

  function feature(p) {
    var art = el('article', 'feature');
    var m = media(p); if (p.page) { var link = el('a'); link.href = p.page; link.className = 'media'; link.setAttribute('aria-label', p.title); link.appendChild(m.firstChild); m = link; }
    art.appendChild(m);
    var b = el('div', 'body');
    b.appendChild(el('span', 'meta-line', [p.subtitle, p.year].filter(Boolean).join(' · ')));
    b.appendChild(el('h2', null, p.title));
    b.appendChild(el('p', null, p.cardExcerpt));
    b.appendChild(chips(p));
    b.appendChild(buttons(p, true));
    art.appendChild(b); return art;
  }

  function card(p) {
    var art = el('article', 'card');
    art.appendChild(media(p));
    var b = el('div', 'body');
    b.appendChild(el('span', 'meta-line', [p.subtitle, p.year].filter(Boolean).join(' · ')));
    b.appendChild(el('h3', null, p.title));
    b.appendChild(el('p', null, p.cardExcerpt));
    b.appendChild(buttons(p, false));
    art.appendChild(b); return art;
  }

  function openDetail(p) {
    var d = $('detail'), box = $('detailInner'); box.innerHTML = '';
    box.appendChild(media(p));
    var b = el('div', 'body');
    b.appendChild(el('span', 'meta-line', [p.role, p.year].filter(Boolean).join(' · ')));
    b.appendChild(el('h2', null, p.title));
    b.appendChild(el('p', 'muted', p.description));
    b.appendChild(chips(p));
    var close = el('button', 'btn small', 'Cerrar'); close.type = 'button'; close.onclick = function () { d.close(); };
    var row = el('div', 'btn-row'); (p.links || []).forEach(function (l) { var a = el('a', 'btn small primary', l.label); a.href = l.url; a.target = '_blank'; a.rel = 'noopener'; row.appendChild(a); });
    row.appendChild(close); b.appendChild(row); box.appendChild(b);
    d.showModal();
  }
  $('detail').addEventListener('click', function (e) { if (e.target === this) this.close(); });

  fetch('data/projects.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (data) {
    var site = data.site || {};
    $('siteTitle').textContent = site.title || 'Proyectos';
    $('siteTagline').textContent = site.tagline || '';
    $('siteLocation').textContent = site.location || '';
    $('brandName').textContent = $('footName').textContent = site.ownerName || 'José';
    if (site.github) $('ghLink').href = site.github;
    var list = (data.projects || []).filter(function (p) { return p.published; }).sort(function (a, b) { return (a.order || 0) - (b.order || 0); });
    var feats = list.filter(function (p) { return p.featured; }), rest = list.filter(function (p) { return !p.featured; });
    feats.forEach(function (p) { $('destacados').appendChild(feature(p)); });
    rest.forEach(function (p) { $('grid').appendChild(card(p)); });
    if (!rest.length) $('todosHead').hidden = true;
  }).catch(function () { $('loadError').hidden = false; });
})();
