(function () {
  'use strict';

  const FALLBACK_COLORS = ['#4a5cff', '#ff5c8a', '#22c1a4', '#f5a623', '#9b59b6', '#e74c3c'];

  const gridEl = document.getElementById('grid');
  const loadErrorEl = document.getElementById('loadError');
  const siteTitleEl = document.getElementById('siteTitle');
  const siteTaglineEl = document.getElementById('siteTagline');

  const overlayEl = document.getElementById('overlay');
  const modalEl = overlayEl.querySelector('.modal');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalBackBtn = document.getElementById('modalBackBtn');
  const modalMediaEl = document.getElementById('modalMedia');
  const modalSubtitleEl = document.getElementById('modalSubtitle');
  const modalTitleEl = document.getElementById('modalTitle');
  const modalMetaEl = document.getElementById('modalMeta');
  const modalDescEl = document.getElementById('modalDesc');
  const modalTagsEl = document.getElementById('modalTags');
  const modalLinksEl = document.getElementById('modalLinks');
  const modalContactEl = document.getElementById('modalContact');

  let site = null;
  let projects = [];
  let lastFocusedEl = null;

  function initials(title) {
    if (!title) return '?';
    const words = title.trim().split(/\s+/).filter(Boolean);
    if (words.length === 0) return '?';
    if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
    return (words[0][0] + words[1][0]).toUpperCase();
  }

  function colorForId(id) {
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
      hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
    }
    return FALLBACK_COLORS[hash % FALLBACK_COLORS.length];
  }

  function buildFallback(project, sizeClass) {
    const div = document.createElement('div');
    div.className = 'card-fallback' + (sizeClass ? ' ' + sizeClass : '');
    div.style.background = colorForId(project.id);
    div.textContent = initials(project.title);
    return div;
  }

  function buildMedia(project, src, alt, container) {
    if (!src) {
      container.appendChild(buildFallback(project));
      return;
    }
    const img = document.createElement('img');
    img.className = 'card-media';
    img.src = src;
    img.alt = alt || project.title;
    img.loading = 'lazy';
    img.onerror = function () {
      img.remove();
      container.appendChild(buildFallback(project));
    };
    container.appendChild(img);
  }

  function renderHeader() {
    siteTitleEl.textContent = site.title || 'Mis Proyectos';
    siteTaglineEl.textContent = site.tagline || '';
  }

  function renderGrid() {
    gridEl.innerHTML = '';

    if (projects.length === 0) {
      const empty = document.createElement('p');
      empty.className = 'empty-state';
      empty.textContent = 'Todavía no hay proyectos publicados. Vuelve pronto.';
      gridEl.appendChild(empty);
      return;
    }

    projects.forEach(function (project) {
      const externalUrl = project.links && project.links[0] && project.links[0].url;
      const card = document.createElement(externalUrl ? 'a' : 'div');
      card.className = 'card';
      if (externalUrl) {
        card.href = externalUrl;
        card.target = '_blank';
        card.rel = 'noopener noreferrer';
        card.setAttribute('aria-label', 'Abrir proyecto: ' + project.title);
      } else {
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.setAttribute('aria-label', 'Ver proyecto: ' + project.title);
      }

      const mediaWrap = document.createElement('div');
      buildMedia(project, project.thumb, project.title, mediaWrap);
      card.appendChild(mediaWrap);

      const body = document.createElement('div');
      body.className = 'card-body';

      const h2 = document.createElement('h2');
      h2.textContent = project.title;
      body.appendChild(h2);

      const p = document.createElement('p');
      p.textContent = project.cardExcerpt || '';
      body.appendChild(p);

      const cta = document.createElement('span');
      cta.className = 'card-cta';
      cta.textContent = externalUrl ? 'Abrir proyecto →' : 'Ver detalle →';
      body.appendChild(cta);

      card.appendChild(body);

      if (!externalUrl) {
        card.addEventListener('click', function () {
          openProject(project.id);
        });
        card.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openProject(project.id);
          }
        });
      }

      gridEl.appendChild(card);
    });
  }

  function findProject(id) {
    return projects.find(function (p) { return p.id === id; }) || null;
  }

  function showProject(project) {
    modalTitleEl.textContent = project.title;
    modalSubtitleEl.textContent = project.subtitle || '';
    modalSubtitleEl.style.display = project.subtitle ? 'block' : 'none';

    const metaParts = [];
    if (project.role) metaParts.push(project.role);
    if (project.year) metaParts.push(String(project.year));
    modalMetaEl.textContent = metaParts.join(' · ');
    modalMetaEl.style.display = metaParts.length ? 'block' : 'none';

    modalDescEl.textContent = project.description || '';

    modalMediaEl.innerHTML = '';
    buildMedia(project, project.hero || project.thumb, project.subtitle || project.title, modalMediaEl);

    modalTagsEl.innerHTML = '';
    (project.tags || []).forEach(function (tag) {
      const li = document.createElement('li');
      li.textContent = tag;
      modalTagsEl.appendChild(li);
    });
    modalTagsEl.style.display = (project.tags || []).length ? 'flex' : 'none';

    modalLinksEl.innerHTML = '';
    (project.links || []).forEach(function (link) {
      const a = document.createElement('a');
      a.href = link.url;
      a.textContent = link.label;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      modalLinksEl.appendChild(a);
    });

    modalContactEl.innerHTML = '';
    if (site.contactEmail) {
      const a = document.createElement('a');
      a.href = 'mailto:' + site.contactEmail;
      a.textContent = 'Contactar por email';
      modalContactEl.appendChild(a);
    }
    if (site.contactLinkedIn) {
      const a = document.createElement('a');
      a.href = site.contactLinkedIn;
      a.textContent = 'LinkedIn';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      modalContactEl.appendChild(a);
    }

    overlayEl.classList.add('open');
    lastFocusedEl = document.activeElement;
    modalCloseBtn.focus();
  }

  function hideModal() {
    overlayEl.classList.remove('open');
    if (lastFocusedEl && typeof lastFocusedEl.focus === 'function') {
      lastFocusedEl.focus();
    }
  }

  function openProject(id) {
    const project = findProject(id);
    if (!project) {
      closeProject();
      return;
    }
    showProject(project);
    try {
      window.history.pushState({ project: id }, '', '#proyecto/' + id);
    } catch (e) { /* ignore */ }
  }

  function closeProject() {
    hideModal();
    try {
      if (window.location.hash) {
        window.history.pushState({}, '', window.location.pathname + window.location.search);
      }
    } catch (e) { /* ignore */ }
  }

  function idFromHash() {
    const m = window.location.hash.match(/^#proyecto\/([a-z0-9-]+)$/i);
    return m ? m[1] : null;
  }

  function handleRoute() {
    const id = idFromHash();
    if (id && findProject(id)) {
      showProject(findProject(id));
    } else {
      hideModal();
    }
  }

  modalCloseBtn.addEventListener('click', closeProject);
  modalBackBtn.addEventListener('click', closeProject);
  overlayEl.addEventListener('click', function (e) {
    if (e.target === overlayEl) closeProject();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlayEl.classList.contains('open')) closeProject();
  });
  window.addEventListener('popstate', handleRoute);

  fetch('data/projects.json')
    .then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    })
    .then(function (data) {
      site = data.site || {};
      projects = (data.projects || [])
        .filter(function (p) { return p.published === true; })
        .sort(function (a, b) { return (a.order || 0) - (b.order || 0); });

      renderHeader();
      renderGrid();
      handleRoute();
    })
    .catch(function (err) {
      console.error('No se pudo cargar data/projects.json', err);
      siteTitleEl.textContent = 'Mis Proyectos';
      siteTaglineEl.textContent = '';
      loadErrorEl.hidden = false;
    });
})();
