#!/usr/bin/env python3
"""ACWW 한글 팬 위키 정적 빌드 스크립트.

content/**/*.md  ->  docs/**/*.html   (GitHub Pages는 docs/ 를 서빙한다)

사용법:  python build.py
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
OUT = ROOT / "docs"

SITE_NAME = "놀러오세요 동물의 숲 근거 위키"
SITE_SHORT = "ACWW 근거 위키"
SITE_TAGLINE = "코드가 말해 주는 놀러오세요 동물의 숲 (Wild World) 이야기"

# 내비게이션: (디렉터리, 라벨, 아이콘, 한 줄 설명, 페이지 순서)
SECTIONS = [
    ("systems", "시스템", "🕰️", "게임이 어떻게 동작하는가 — 시간, 세이브, 날씨, 주민, 마을, 이벤트, 대화",
     ["time-and-rtc", "save-data", "town", "villagers", "player", "economy",
      "weather-and-seasons", "events-and-calendar", "dialogue", "input-and-touch",
      "rng", "network", "audio"]),
    ("data", "데이터", "📦", "테이블에 무엇이 들어 있는가 — 아이템, 주민, 물고기와 곤충, 음악, 아카이브, ROM",
     ["items", "villagers", "fish-and-bugs", "music", "archives", "rom-layout"]),
    ("engine", "엔진", "⚙️", "프로그램이 어떻게 만들어졌는가 — 부팅, 오버레이, 씬, 메모리, 스레드, 그래픽스, 텍스트",
     ["boot-and-entry", "overlays", "scenes-and-channels", "display-objects", "memory-map",
      "threads-and-interrupts", "file-system", "graphics-pipeline", "text-and-messages"]),
    ("experiments", "실험", "🔬", "주장을 어떻게 확인하는가 — 재현 가능한 레시피와 실행 기록",
     ["off-recipe", "two-tap-town-recipe", "touch-calibration", "rtc-hour-sweep",
      "save-store-probe", "rng-determinism", "silent-audio-probe"]),
    ("audits", "감사", "🔍", "위키가 위키를 읽는다 — 감사 패스별 발견 사항과 적용된 수정",
     ["consistency", "game-systems", "data-formats", "hardware-services", "3d-engine", "sdk-names"]),
]
TOP_PAGES = [("glossary", "용어집", "📖"), ("about", "이 위키에 대하여", "🍃"), ("style", "문서 규칙", "✏️")]
TOP_DESC = {"glossary": "위키 전반에서 쓰는 용어와 그것을 정의하는 함수·주소",
            "about": "근거 등급, 문서 층위, 이 위키가 하지 않는 것",
            "style": "문서 템플릿과 아홉 가지 규칙"}

GRADE_INFO = {
    "S": ("소스", "매칭된 함수나 심볼 테이블에서 읽은 것"),
    "E": ("실험", "PC 포트의 스크립트 실행에서 관측한 것"),
    "O": ("오라클", "같은 레시피의 DeSmuME 레퍼런스에서 관측한 것"),
    "H": ("가설", "추론했지만 아직 측정하지 않은 것"),
    "P": ("공개 기록", "GBATEK, 공개된 NitroSDK 소스 등 외부 공개 문서와 대조한 것 (감사 문서에서만 쓴다)"),
}

MD_EXT = ["tables", "fenced_code", "toc", "attr_list", "sane_lists", "md_in_html", "smarty"]
MD_CFG = {"toc": {"toc_depth": "2-3", "permalink": False, "slugify": lambda v, s: slugify(v)},
          "smarty": {"smart_dashes": True, "smart_quotes": False, "smart_ellipses": False, "smart_angled_quotes": False}}

CITE_RE = re.compile(r"\[((?:[SEOHP])(?:\s*\+\s*[SEOHP])*)\s*:\s*((?:(?!\]).)*?)\]", re.S)
LINK_RE = re.compile(r'href="([^"#:]+?\.md)(#[^"]*)?"')


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^\w\s가-힣-]", "", value).strip().lower()
    value = re.sub(r"[\s_]+", "-", value)
    return value or "section"


def load_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(tpl: str, **ctx: str) -> str:
    for k, v in ctx.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def rel_root(out_path: Path) -> str:
    depth = len(out_path.relative_to(OUT).parts) - 1
    return "../" * depth if depth else "./"


def md_to_html_path(link: str) -> str:
    if link.endswith("README.md"):
        return link[: -len("README.md")] + "index.html"
    return link[:-3] + ".html"


def cite_html(m: re.Match) -> str:
    grades = re.sub(r"\s+", "", m.group(1))
    body = re.sub(r"\s*\n\s*", " ", m.group(2))
    letters = grades.split("+")
    badges = "".join(f'<b class="g g-{g}" title="{GRADE_INFO[g][0]}">{g}</b>' for g in letters)
    return (f'<span class="cite" data-grade="{grades}"><span class="cite-badge">{badges}</span>'
            f'<span class="cite-body">{body}</span></span>')


def postprocess(body: str) -> str:
    body = CITE_RE.sub(cite_html, body)
    body = LINK_RE.sub(lambda m: f'href="{md_to_html_path(m.group(1))}{m.group(2) or ""}"', body)
    # 표를 가로 스크롤 컨테이너로 감싼다
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return body


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


class Page:
    def __init__(self, src: Path):
        self.src = src
        self.rel = src.relative_to(CONTENT)  # e.g. systems/town.md
        self.section = self.rel.parts[0] if len(self.rel.parts) > 1 else ""
        self.slug = self.rel.stem
        self.is_index = self.slug == "README"
        out_rel = Path(md_to_html_path(self.rel.as_posix()))
        self.out = OUT / out_rel
        self.url = out_rel.as_posix()
        raw = src.read_text(encoding="utf-8")
        m = re.match(r"#\s+(.+)", raw)
        self.title = m.group(1).strip() if m else self.slug
        raw = raw[m.end():] if m else raw
        sm = re.search(r"<!--\s*source:\s*(.+?)\s*-->", raw)
        self.source = sm.group(1) if sm else None
        raw = re.sub(r"<!--\s*source:.*?-->\s*", "", raw, count=1)
        self.raw = raw
        md = markdown.Markdown(extensions=MD_EXT, extension_configs=MD_CFG)
        self.body = postprocess(md.convert(raw))
        self.toc = md.toc if md.toc_tokens else ""
        self.toc_tokens = md.toc_tokens
        sm2 = re.search(r"\*\*요약\.\*\*\s*(.+?)(?:\n\n|\Z)", raw, re.S)
        self.summary = re.sub(r"\s+", " ", sm2.group(1)).strip() if sm2 else ""
        self.summary = re.sub(r"\[[SEOHP+\s]+:[^\]]*\]", "", self.summary)
        self.summary = re.sub(r"`", "", self.summary)
        self.grade_counts = {g: 0 for g in GRADE_INFO}
        for m in CITE_RE.finditer(raw):
            for g in re.sub(r"\s+", "", m.group(1)).split("+"):
                self.grade_counts[g] += 1


def build_nav(pages: dict[str, Page], root: str, current: Page | None) -> str:
    out = []
    for key, label, icon, _desc, order in SECTIONS:
        idx = pages.get(f"{key}/README.md")
        active = current is not None and current.section == key
        out.append(f'<details class="nav-sec" {"open" if active else ""}>')
        href = f"{root}{key}/index.html"
        out.append(f'<summary><span class="nav-icon">{icon}</span><a href="{href}">{label}</a></summary><ul>')
        for slug in order:
            p = pages.get(f"{key}/{slug}.md")
            if not p:
                continue
            cls = ' class="active"' if current is p else ""
            out.append(f'<li{cls}><a href="{root}{p.url}">{html.escape(p.title)}</a></li>')
        out.append("</ul></details>")
    out.append('<ul class="nav-top">')
    for slug, label, icon in TOP_PAGES:
        p = pages.get(f"{slug}.md")
        if not p:
            continue
        cls = ' class="active"' if current is p else ""
        out.append(f'<li{cls}><a href="{root}{p.url}"><span class="nav-icon">{icon}</span>{html.escape(p.title)}</a></li>')
    out.append("</ul>")
    return "\n".join(out)


def section_meta(key: str):
    for k, label, icon, desc, order in SECTIONS:
        if k == key:
            return label, icon, desc, order
    return None


def breadcrumbs(page: Page, root: str) -> str:
    parts = [f'<a href="{root}index.html">🏠 홈</a>']
    if page.section:
        meta = section_meta(page.section)
        label = meta[0] if meta else page.section
        if page.is_index:
            parts.append(f"<span>{label}</span>")
        else:
            parts.append(f'<a href="{root}{page.section}/index.html">{label}</a>')
            parts.append(f"<span>{html.escape(page.title)}</span>")
    else:
        parts.append(f"<span>{html.escape(page.title)}</span>")
    return ' <span class="sep">›</span> '.join(parts)


def prev_next(page: Page, pages: dict[str, Page], root: str) -> str:
    meta = section_meta(page.section) if page.section else None
    if not meta or page.is_index:
        return ""
    order = [pages[f"{page.section}/{s}.md"] for s in meta[3] if f"{page.section}/{s}.md" in pages]
    if page not in order:
        return ""
    i = order.index(page)
    prev_p = order[i - 1] if i > 0 else None
    next_p = order[i + 1] if i + 1 < len(order) else None
    a = (f'<a class="pn prev" href="{root}{prev_p.url}"><small>◀ 이전</small>{html.escape(prev_p.title)}</a>'
         if prev_p else '<span class="pn"></span>')
    b = (f'<a class="pn next" href="{root}{next_p.url}"><small>다음 ▶</small>{html.escape(next_p.title)}</a>'
         if next_p else '<span class="pn"></span>')
    return f'<nav class="prevnext">{a}{b}</nav>'


def grade_bar(page: Page) -> str:
    total = sum(page.grade_counts.values())
    if not total:
        return ""
    chips = "".join(
        f'<span class="gchip g-{g}"><b>{g}</b> {n}</span>' for g, n in page.grade_counts.items() if n)
    return f'<div class="gradebar" title="이 문서의 출처 태그 수"><span class="gradebar-label">근거</span>{chips}</div>'


def section_cards(key: str, pages: dict[str, Page], root: str) -> str:
    meta = section_meta(key)
    if not meta:
        return ""
    cards = []
    for slug in meta[3]:
        p = pages.get(f"{key}/{slug}.md")
        if not p:
            continue
        summ = html.escape(p.summary[:110] + ("…" if len(p.summary) > 110 else ""))
        cards.append(f'<a class="card" href="{root}{p.url}"><h3>{html.escape(p.title)}</h3><p>{summ}</p></a>')
    return '<div class="cards">' + "".join(cards) + "</div>"


def toc_html(page: Page) -> str:
    if not page.toc_tokens:
        return ""
    def walk(tokens, depth=0):
        items = []
        for t in tokens:
            items.append(f'<li><a href="#{t["id"]}">{t["name"]}</a>' +
                         (f'<ul>{walk(t["children"], depth + 1)}</ul>' if t["children"] and depth < 1 else "") + "</li>")
        return "".join(items)
    return f'<nav class="toc" aria-label="목차"><div class="toc-title">목차</div><ul>{walk(page.toc_tokens)}</ul></nav>'


def build():
    if OUT.exists():
        for child in OUT.iterdir():
            if child.name == ".nojekyll":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    OUT.mkdir(exist_ok=True)
    (OUT / ".nojekyll").write_text("")
    shutil.copytree(ASSETS, OUT / "assets")

    pages: dict[str, Page] = {}
    for src in sorted(CONTENT.rglob("*.md")):
        p = Page(src)
        pages[p.rel.as_posix()] = p

    base = load_template("base.html")
    home_tpl = load_template("home.html")
    search_index = []

    for key, p in pages.items():
        root = rel_root(p.out)
        extra = ""
        if p.is_index:
            extra = section_cards(p.section, pages, root)
        src_line = (f'<div class="source-line">원문: <code>{html.escape(p.source)}</code> (영문, 기록 문서)</div>'
                    if p.source else "")
        article = (f'<div class="crumbs">{breadcrumbs(p, root)}</div>'
                   f'<header class="page-head"><h1>{html.escape(p.title)}</h1>{grade_bar(p)}{src_line}</header>'
                   f'{extra}<div class="md">{p.body}</div>{prev_next(p, pages, root)}')
        page_html = render(base, root=root, title=f"{html.escape(p.title)} · {SITE_SHORT}",
                           site_name=SITE_NAME, site_short=SITE_SHORT, nav=build_nav(pages, root, p),
                           toc=toc_html(p), content=article, body_class="page",
                           description=html.escape(p.summary[:150]))
        p.out.parent.mkdir(parents=True, exist_ok=True)
        p.out.write_text(page_html, encoding="utf-8")

        # 검색 색인: 섹션(h2) 단위
        plain_sections = re.split(r"(?m)^##\s+", p.raw)
        search_index.append({"u": p.url, "t": p.title, "s": section_meta(p.section)[0] if p.section else "",
                             "h": "", "x": re.sub(r"\s+", " ", strip_tags(plain_sections[0]))[:600]})
        for sec in plain_sections[1:]:
            head, _, rest = sec.partition("\n")
            search_index.append({"u": p.url + "#" + slugify(head), "t": p.title,
                                 "s": section_meta(p.section)[0] if p.section else "",
                                 "h": head.strip(), "x": re.sub(r"\s+", " ", rest)[:1500]})

    # 홈
    root = "./"
    sec_cards = []
    for key, label, icon, desc, order in SECTIONS:
        n = sum(1 for s in order if f"{key}/{s}.md" in pages)
        sec_cards.append(f'<a class="sec-card sec-{key}" href="{key}/index.html"><span class="sec-icon">{icon}</span>'
                         f'<h3>{label}</h3><p>{desc}</p><span class="sec-count">{n}개 문서</span></a>')
    for slug, label, icon in TOP_PAGES:
        if f"{slug}.md" in pages:
            sec_cards.append(f'<a class="sec-card sec-top" href="{slug}.html"><span class="sec-icon">{icon}</span>'
                             f'<h3>{label}</h3><p>{TOP_DESC.get(slug, "")}</p></a>')
    grade_rows = "".join(
        f'<li><b class="g g-{g}">{g}</b><span><strong>{n}</strong> — {d}</span></li>' for g, (n, d) in GRADE_INFO.items())
    featured = []
    for key, slug in [("systems", "time-and-rtc"), ("systems", "town"), ("systems", "villagers"),
                      ("data", "items"), ("engine", "boot-and-entry"), ("experiments", "two-tap-town-recipe")]:
        p = pages.get(f"{key}/{slug}.md")
        if p:
            featured.append(f'<a class="card" href="{p.url}"><h3>{html.escape(p.title)}</h3>'
                            f'<p>{html.escape(p.summary[:120])}…</p></a>')
    total_pages = len(pages)
    total_cites = sum(sum(p.grade_counts.values()) for p in pages.values())
    home_body = render(home_tpl, sec_cards="".join(sec_cards), grade_rows=grade_rows,
                       featured="".join(featured), total_pages=str(total_pages),
                       total_cites=f"{total_cites:,}", tagline=SITE_TAGLINE)
    (OUT / "index.html").write_text(
        render(base, root=root, title=SITE_NAME, site_name=SITE_NAME, site_short=SITE_SHORT,
               nav=build_nav(pages, root, None), toc="", content=home_body, body_class="home",
               description=html.escape(SITE_TAGLINE)), encoding="utf-8")

    (OUT / "search-index.json").write_text(json.dumps(search_index, ensure_ascii=False), encoding="utf-8")
    (OUT / "404.html").write_text(
        render(base, root="/acww-wiki/", title="길을 잃었어요 · " + SITE_SHORT, site_name=SITE_NAME,
               site_short=SITE_SHORT, nav=build_nav(pages, "/acww-wiki/", None), toc="",
               content='<div class="md notfound"><h1>이 길은 막혀 있어요</h1><p>찾는 문서가 없다. '
                       '<a href="/acww-wiki/index.html">홈으로</a> 돌아가거나 검색해 보자.</p></div>',
               body_class="page", description=""), encoding="utf-8")
    print(f"built {total_pages} pages, {total_cites} citations -> {OUT}")


if __name__ == "__main__":
    build()
