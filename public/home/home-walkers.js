// Main page: a few villagers stroll slowly along the bottom of the hero card.
// Frames are pre-rendered PNG strips (scripts/render_villager_walkers.py -> home/walkers/), no model data.
(() => {
  const lane = document.querySelector('.hh-walk');
  if (!lane) return;
  const BASE = '/acww-wiki';
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const MAX_AT_ONCE = 4;
  const SCALE = 0.75;
  let list = [], active = 0;

  function spawn() {
    if (!list.length || active >= MAX_AT_ONCE || document.hidden) return;
    const walking = new Set([...lane.querySelectorAll('.hh-walker')].map(e => e.dataset.name));
    const pool = list.filter(x => !walking.has(x.name));  // never the same villager twice at once
    const w = pool[Math.floor(Math.random() * pool.length)];
    if (!w) return;
    const scale = SCALE;  // sprite frames are 112 px boxes; walkers stay small
    const fw = Math.round(w.frame_w * scale), fh = Math.round(w.frame_h * scale);
    const toRight = Math.random() < 0.5;
    const span = lane.clientWidth + fw * 2;
    // the outer box moves (and carries the name bubble); the inner sprite flips and steps through the frames
    const el = document.createElement('div');
    el.className = 'hh-walker';
    el.style.cssText = `width:${fw}px;height:${fh}px;bottom:${Math.round((w.frame_h - w.baseline_y) * scale) * -1}px;`;
    el.dataset.name = w.name || '';
    el.setAttribute('aria-label', w.name || '');
    const sprite = document.createElement('div');
    sprite.className = 'hh-sprite';
    sprite.style.cssText = `background-image:url(${BASE}/home/walkers/${w.id}.png);background-size:${fw * w.frames}px ${fh}px;`
      + `--frames:${w.frames};--strip:-${fw * w.frames}px;--cycle:${w.cycle_seconds_suggested || 1}s;`
      + (toRight ? '' : 'transform:scaleX(-1);');
    el.appendChild(sprite);
    lane.appendChild(el);
    active++;
    // move exactly as far per walk cycle as the feet step, so they don't skate
    const cycle = w.cycle_seconds_suggested || 1.2;
    const speed = (w.travel_px_per_cycle_no_slide || 21) * scale / cycle;
    const dur = span / speed * 1000;
    const from = toRight ? -fw : lane.clientWidth + fw, to = toRight ? lane.clientWidth + fw : -fw;
    const anim = el.animate([{transform: `translateX(${from}px)`}, {transform: `translateX(${to}px)`}], {duration: dur, easing: 'linear'});
    anim.onfinish = () => { el.remove(); active--; };
  }

  fetch(`${BASE}/home/walkers/manifest.json`).then(r => r.json()).then(m => {
    list = Array.isArray(m) ? m : (m.walkers || []);
    if (!list.length) return;
    if (still) {  // no motion: one villager standing still in the corner
      const w = list[0], s = SCALE;
      lane.innerHTML = `<div class="hh-walker still" data-name="${w.name || ''}" style="width:${Math.round(w.frame_w * s)}px;height:${Math.round(w.frame_h * s)}px;right:1.5rem;bottom:0"><div class="hh-sprite" style="background-image:url(${BASE}/home/walkers/${w.id}.png);background-size:${Math.round(w.frame_w * s) * w.frames}px ${Math.round(w.frame_h * s)}px"></div></div>`;
      return;
    }
    spawn();
    setTimeout(spawn, 6000);
    setInterval(spawn, 16000);
  }).catch(() => {});
})();
