// Main-page monthly calendar. Fills <div class="home-cal"> from <base>/home/calendar-data.json
// (built by scripts/build_home_calendar.py). Uses this device's date as the game's DS clock date.
(() => {
  // every page stands on the season's tile ground (faint on article pages): set it from today's date first
  const SEASON_OF = m => (m === 12 || m <= 2) ? 'winter' : m <= 5 ? 'spring' : m <= 8 ? 'summer' : 'autumn';
  document.documentElement.dataset.season = SEASON_OF(new Date().getMonth() + 1);
  const root = document.querySelector('.home-cal');
  if (!root) return;
  root.classList.add('not-content');  // opt out of Starlight prose spacing
  const BASE = root.dataset.base || '/acww-wiki';
  const WD = '일월화수목금토';
  const SEASON = {12: 'winter', 1: 'winter', 2: 'winter', 3: 'spring', 4: 'spring', 5: 'spring', 6: 'summer', 7: 'summer', 8: 'summer', 9: 'autumn', 10: 'autumn', 11: 'autumn'};
  const SEASON_KO = {winter: '겨울', spring: '봄', summer: '여름', autumn: '가을'};
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  // data-links="off" (public main page before the articles are published): names stay plain text
  const LINKS = root.dataset.links !== 'off';
  const link = (page, text) => LINKS ? `<a href="${BASE}/${page}/">${esc(text)}</a>` : esc(text);
  const dim = (y, m) => new Date(y, m, 0).getDate();
  const nthWeekday = (y, m, n, wd) => 1 + ((wd - new Date(y, m - 1, 1).getDay() + 7) % 7) + 7 * (n - 1);
  const ymd = d => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  const md = d => `${d.getMonth() + 1}월 ${d.getDate()}일 ${WD[d.getDay()]}요일`;

  let data, view;
  const today = new Date();

  function monthItems(y, m) {
    const days = {}, add = (d, it) => { if (d.getFullYear() === y && d.getMonth() + 1 === m) (days[d.getDate()] = days[d.getDate()] || []).push(it); };
    const festivalDays = new Set();
    for (const ev of data.events) {
      const r = ev.rule;
      for (const mm of [m - 1, m, m + 1]) {
        const yy = y + (mm < 1 ? -1 : mm > 12 ? 1 : 0), mon = ((mm + 11) % 12) + 1;
        if (!r.months.includes(mon)) continue;
        let starts = [];
        if (r.day) starts = [new Date(yy, mon - 1, r.day)];
        else if (r.every !== undefined) { for (let d = 1; d <= dim(yy, mon); d++) if (new Date(yy, mon - 1, d).getDay() === r.every) starts.push(new Date(yy, mon - 1, d)); }
        else { const d = nthWeekday(yy, mon, r.nth, r.weekday); if (d <= dim(yy, mon)) starts = [new Date(yy, mon - 1, d + (r.offset || 0))]; }
        for (const s of starts) {
          const n = r.days || 1;
          for (let k = 0; k < n; k++) {
            const d = new Date(s.getFullYear(), s.getMonth(), s.getDate() + k);
            if (n > 1) festivalDays.add(ymd(d));
            add(d, {kind: ev.kind, name: ev.name, time: ev.time, short: ev.short, page: ev.page, span: n > 1 ? (k === 0 ? 'start' : k === n - 1 ? 'end' : 'mid') : null});
          }
        }
      }
    }
    for (const w of data.weekly) {
      for (let d = 1; d <= dim(y, m); d++) {
        const dt = new Date(y, m - 1, d);
        if (dt.getDay() !== w.weekday) continue;
        if (w.skip && ((/festival-week/.test(w.skip) && festivalDays.has(ymd(dt))) || (m === 12 && d === 31) || (m === 1 && d === 1))) continue;
        add(dt, {kind: 'visitor', name: w.name, time: w.time, short: w.short, page: w.page});
      }
    }
    for (const b of data.birthdays) if (b.m === m) add(new Date(y, m - 1, b.d), {kind: 'birthday', name: b.name, id: b.id, note: b.species, page: 'villager-roster'});
    for (const s of data.seasons) if (s.md[0] === m) add(new Date(y, m - 1, s.md[1]), {kind: 'season', name: s.text, page: s.page});
    const order = ['festival', 'holiday', 'contest', 'market', 'visitor', 'season', 'birthday'];
    for (const d in days) days[d].sort((a, b) => order.indexOf(a.kind) - order.indexOf(b.kind));
    return days;
  }

  function face(b, big) {
    const img = data.faces ? `<img src="${BASE}/home/faces/${b.id}.png" alt="" loading="lazy" onerror="this.remove()">` : '';
    return `<span class="face${big ? ' big' : ''}">${img}</span>`;
  }

  function cell(d, its, wd, isNow) {
    const fest = its.find(i => i.kind === 'festival');
    const lines = its.filter(i => ['holiday', 'contest', 'market', 'visitor'].includes(i.kind));
    const bds = its.filter(i => i.kind === 'birthday');
    const season = its.find(i => i.kind === 'season');
    const cls = ['c', wd === 0 ? 'sun' : wd === 6 ? 'sat' : '', isNow ? 'now' : '', fest ? 'band' : ''].join(' ');
    return `<div class="${cls}">
      <div class="top"><span class="n">${d}</span>${fest && (fest.span === 'start' || wd === 0) ? `<a class="bandname" href="${BASE}/${fest.page}/">${esc(fest.name)}</a>` : ''}</div>
      ${lines.length ? `<ul class="ls">${lines.map(i => `<li class="k-${i.kind}"><a href="${BASE}/${i.page}/">${esc(i.name)}</a><span>${esc(i.short || '')}</span></li>`).join('')}</ul>` : ''}
      ${season ? `<a class="se" href="${BASE}/${season.page}/" title="${esc(season.name)}">계절 변화</a>` : ''}
      ${bds.length ? `<div class="bds">${bds.map(b => `<a class="bd" href="${BASE}/villager-roster/" title="${esc(b.name)}(${esc(b.note)})의 생일">${face(b)}<span>${esc(b.name)}</span></a>`).join('')}</div>` : ''}
    </div>`;
  }

  function draw() {
    const [y, m] = view, items = monthItems(y, m);
    const first = new Date(y, m - 1, 1).getDay(), n = dim(y, m);
    const isThisMonth = today.getFullYear() === y && today.getMonth() + 1 === m;
    root.dataset.season = SEASON[m];
    const shell = root.closest('.home-shell');
    if (shell) { shell.dataset.season = SEASON[m]; document.documentElement.dataset.season = SEASON[m]; }
    let cells = '';
    for (let i = 0; i < first; i++) cells += '<div class="c pad"></div>';
    for (let d = 1; d <= n; d++) cells += cell(d, items[d] || [], (first + d - 1) % 7, isThisMonth && d === today.getDate());
    const tail = (7 - ((first + n) % 7)) % 7;
    for (let i = 0; i < tail; i++) cells += '<div class="c pad"></div>';
    const prevM = m === 1 ? [y - 1, 12] : [y, m - 1];
    const nextM = m === 12 ? [y + 1, 1] : [y, m + 1];
    root.innerHTML = `
      <div class="hc-stage">
        <header class="hc-head">
          <div class="hc-month"><span class="hc-m">${m}<span class="u">월</span></span><span class="hc-y">${y}년 ${SEASON_KO[SEASON[m]]}</span></div>
          <nav class="hc-nav" aria-label="달 이동">
            <button type="button" data-go="${prevM}" aria-label="이전 달">←</button>
            <button type="button" data-go="${today.getFullYear()},${today.getMonth() + 1}" ${isThisMonth ? 'disabled' : ''}>이번 달</button>
            <button type="button" data-go="${nextM}" aria-label="다음 달">→</button>
            <button type="button" class="hc-save" data-save="cal" title="달력을 WebP 그림으로 저장">달력 저장</button>
          </nav>
        </header>
        <section class="hc-cal glass">
          <div class="hc-wd">${[...WD].map((w, i) => `<span class="${i === 0 ? 'sun' : i === 6 ? 'sat' : ''}">${w}</span>`).join('')}</div>
          <div class="hc-grid">${cells}</div>
        </section>
        ${creatureBlock(m)}
      </div>`;
    root.querySelectorAll('[data-go]').forEach(b => b.onclick = () => { view = b.dataset.go.split(',').map(Number); draw(); });
    root.querySelectorAll('[data-save]').forEach(b => b.onclick = () => saveImage(b));
  }

  function strip(months, m) {
    return `<span class="strip" aria-label="${months.join('·')}월에 나온다">${Array.from({length: 12}, (_, i) =>
      `<i class="${months.includes(i + 1) ? 'on' : ''}${i + 1 === m ? ' cur' : ''}"></i>`).join('')}</span>`;
  }

  function pic(c, fam) {
    return data.pics && c.pic != null
      ? `<span class="pic"><img src="${BASE}/home/creatures/${fam}/${String(c.pic).padStart(2, '0')}.png" alt="" loading="lazy" onerror="this.remove()"></span>` : '';
  }

  function creatureBlock(m) {
    const prev = m === 1 ? 12 : m - 1, next = m === 12 ? 1 : m + 1;
    const row = (c, fam) => `<li>${pic(c, fam)}<span class="nm">${esc(c.name)}</span><span class="pl">${esc(c.place)}</span>${strip(c.months, m)}<span class="pr">${c.price.toLocaleString()}<small>벨</small></span></li>`;
    const col = (list, page, label, fam) => {
      const now = list.filter(c => c.months.includes(m)).sort((a, b) => b.price - a.price);
      const fresh = now.filter(c => !c.months.includes(prev));
      const last = now.filter(c => !c.months.includes(next));
      const rest = now.filter(c => !fresh.includes(c) && !last.includes(c));
      return `<div class="cr-col">
        <div class="cr-head"><h3>${link(page, label)}</h3><span class="cr-count"><b>${now.length}</b>종</span></div>
        ${fresh.length ? `<p class="cr-sub new">이달부터</p><ul class="cr-list">${fresh.map(c => row(c, fam)).join('')}</ul>` : ''}
        ${last.length ? `<p class="cr-sub last">이달까지</p><ul class="cr-list">${last.map(c => row(c, fam)).join('')}</ul>` : ''}
        ${rest.length ? `<p class="cr-sub">한창</p><ul class="cr-cards">${rest.map(c => `<li title="${esc(c.place)} · ${c.months.join('·')}월">${pic(c, fam)}<span class="nm">${esc(c.name)}</span><span class="pl">${esc(c.place)}</span><span class="pr">${c.price.toLocaleString()}<small>벨</small></span></li>`).join('')}</ul>` : ''}
      </div>`;
    };
    return `<section class="hc-creatures glass">
      <div class="cr-title"><h2>${m}월의 생물</h2><button type="button" class="hc-save" data-save="cr" title="생물 목록을 WebP 그림으로 저장">생물 저장</button></div>
      <div class="cr-cols">${col(data.fish, 'fishing', '물고기', 'fish')}${col(data.bugs, 'bug-catching', '곤충', 'bug')}</div>
    </section>`;
  }

  // Image export: a detached copy of the section is laid out at a fixed width over the seasonal
  // backdrop and rasterised with html-to-image (loaded only when a save button is pressed).
  let libLoading = null;
  function loadLib() {
    return libLoading = libLoading || new Promise((res, rej) => {
      if (window.htmlToImage) return res(window.htmlToImage);
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js';
      s.onload = () => res(window.htmlToImage); s.onerror = () => { libLoading = null; rej(new Error('load')); };
      document.head.appendChild(s);
    });
  }
  async function saveImage(btn) {
    const kind = btn.dataset.save, [y, m] = view, label = btn.textContent;
    btn.disabled = true; btn.textContent = '저장 중…';
    let box, host;
    try {
      const lib = await loadLib();
      box = document.createElement('div');
      box.className = 'home-cal hc-export not-content';
      box.dataset.season = root.dataset.season;
      const parts = kind === 'cal' ? [root.querySelector('.hc-head'), root.querySelector('.hc-cal')] : [root.querySelector('.hc-creatures')];
      const stage = document.createElement('div'); stage.className = 'hc-stage';
      for (const p of parts) stage.appendChild(p.cloneNode(true));
      stage.querySelectorAll('.hc-nav, .hc-save').forEach(e => e.remove());
      box.appendChild(stage);
      host = document.createElement('div');  // zero-size clipping host keeps the copy invisible but laid out normally
      host.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;overflow:hidden;pointer-events:none';
      host.appendChild(box); document.body.appendChild(host);
      const imgs = [...box.querySelectorAll('img')];
      imgs.forEach(i => { i.loading = 'eager'; i.src = i.src; });  // lazy images never load off-screen
      const wait = ms => new Promise(r => setTimeout(r, ms));
      await Promise.race([Promise.all(imgs.map(i => i.decode().catch(() => 0))), wait(4000)]);
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const bg = getComputedStyle(document.body).backgroundColor;
      const canvas = await lib.toCanvas(box, {pixelRatio: 3, backgroundColor: bg});
      // WebP where the browser can encode it (Safari falls back to PNG and the name follows the real type)
      const blob = await new Promise(r => canvas.toBlob(r, 'image/webp', 0.95));
      const ext = blob && blob.type === 'image/webp' ? 'webp' : 'png';
      const url = URL.createObjectURL(blob || await new Promise(r => canvas.toBlob(r, 'image/png')));
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      const a = document.createElement('a');
      a.href = url; a.download = `acww-${kind === 'cal' ? 'calendar' : 'creatures'}-${y}-${String(m).padStart(2, '0')}.${ext}`;
      document.body.appendChild(a); a.click(); a.remove();
    } catch (e) {
      alert('그림으로 저장하지 못했다.');
    } finally {
      if (host) host.remove();
      btn.disabled = false; btn.textContent = label;
    }
  }

  fetch(`${BASE}/home/calendar-data.json`).then(r => r.json()).then(d => {
    data = d; view = [today.getFullYear(), today.getMonth() + 1]; draw();
  }).catch(() => { root.innerHTML = '<p>달력 자료를 불러오지 못했다.</p>'; });
})();
