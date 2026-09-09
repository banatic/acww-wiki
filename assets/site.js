(function () {
  const root = window.ACWW_ROOT || "./";

  // ---- 모바일 메뉴
  const btn = document.getElementById("menuBtn");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("backdrop");
  function closeMenu() { sidebar.classList.remove("open"); backdrop.classList.remove("show"); btn.setAttribute("aria-expanded", "false"); }
  btn.addEventListener("click", () => {
    const open = !sidebar.classList.contains("open");
    sidebar.classList.toggle("open", open); backdrop.classList.toggle("show", open);
    btn.setAttribute("aria-expanded", String(open));
  });
  backdrop.addEventListener("click", closeMenu);

  // ---- 출처 펼치기 토글 (localStorage 기억)
  const citeToggle = document.getElementById("citeToggle");
  let pref = false;
  try { pref = localStorage.getItem("acww-cites") === "1"; } catch (e) {}
  document.body.classList.toggle("cites-open", pref);
  if (citeToggle) {
    citeToggle.checked = pref;
    citeToggle.addEventListener("change", () => {
      document.body.classList.toggle("cites-open", citeToggle.checked);
      try { localStorage.setItem("acww-cites", citeToggle.checked ? "1" : "0"); } catch (e) {}
    });
  }
  // 배지를 누르면 그 출처만 토글
  document.querySelectorAll(".cite").forEach((c) => {
    c.querySelector(".cite-badge").addEventListener("click", (e) => { e.stopPropagation(); c.classList.toggle("pinned"); });
  });

  // ---- 현재 절 하이라이트 (목차)
  const tocLinks = Array.from(document.querySelectorAll(".toc a"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    const map = new Map();
    tocLinks.forEach((a) => { const el = document.getElementById(decodeURIComponent(a.hash.slice(1))); if (el) map.set(el, a); });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { tocLinks.forEach((a) => a.classList.remove("cur")); map.get(en.target).classList.add("cur"); } });
    }, { rootMargin: "-10% 0px -80% 0px" });
    map.forEach((_, el) => io.observe(el));
  }

  // ---- 검색
  const form = document.getElementById("searchForm");
  const input = document.getElementById("searchInput");
  const results = document.getElementById("searchResults");
  let index = null, loading = null;
  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!loading) loading = fetch(root + "search-index.json").then((r) => r.json()).then((j) => (index = j));
    return loading;
  }
  function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function snippet(text, q) {
    const i = text.toLowerCase().indexOf(q.toLowerCase());
    const start = Math.max(0, i - 50);
    let s = text.slice(start, start + 140);
    if (i >= 0) s = esc(s).replace(new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig"), (m) => "<mark>" + m + "</mark>");
    else s = esc(s);
    return (start > 0 ? "…" : "") + s + "…";
  }
  function search(q) {
    q = q.trim();
    if (q.length < 1) { results.hidden = true; results.innerHTML = ""; return; }
    loadIndex().then((idx) => {
      const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      const scored = [];
      for (const e of idx) {
        const t = (e.t + " " + e.h).toLowerCase(), x = e.x.toLowerCase();
        let score = 0, ok = true;
        for (const term of terms) {
          if (t.includes(term)) score += 10;
          else if (x.includes(term)) score += 1;
          else { ok = false; break; }
        }
        if (ok) scored.push([score, e]);
      }
      scored.sort((a, b) => b[0] - a[0]);
      const top = scored.slice(0, 12);
      if (!top.length) { results.innerHTML = '<div class="sr-empty">검색 결과가 없다. 다른 말로 찾아보자.</div>'; results.hidden = false; return; }
      results.innerHTML = top.map(([, e]) =>
        `<a class="sr" href="${root}${e.u}"><span class="sr-sec">${esc(e.s || "")}</span><b>${esc(e.t)}</b>${e.h ? ' <span class="sr-h">› ' + esc(e.h) + "</span>" : ""}<span class="sr-x">${snippet(e.x, terms[0])}</span></a>`).join("");
      results.hidden = false;
    });
  }
  let timer;
  input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => search(input.value), 120); });
  input.addEventListener("focus", () => { if (results.innerHTML) results.hidden = false; });
  form.addEventListener("submit", (e) => { e.preventDefault(); search(input.value); const first = results.querySelector("a"); if (first && input.value.trim()) first.focus(); });
  document.addEventListener("click", (e) => { if (!form.contains(e.target)) results.hidden = true; });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { results.hidden = true; input.blur(); }
    if (e.key === "/" && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); input.focus(); }
  });
})();
