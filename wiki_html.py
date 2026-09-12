"""번역 문서의 원문 앵커, 링크, 중첩된 출처 표시를 보존한다."""
from __future__ import annotations

import html
import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import quote, unquote, urlsplit


def prepare_markdown(text: str) -> str:
    """원문의 열 수가 어긋난 구분선만 표시 단계에서 머리글에 맞춘다."""
    lines = text.splitlines(keepends=True)
    fence = None
    for i, line in enumerate(lines):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence or not i or not re.fullmatch(r'\|(?:\s*:?-+:?\s*\|)+\s*', line):
            continue
        header = lines[i-1].strip()
        if not header.startswith('|'):
            continue
        columns = len(re.split(r'(?<!\\)\|', header.strip('|')))
        parts = line.strip().strip('|').split('|')
        if len(parts) != columns:
            parts = (parts + ['---'] * columns)[:columns]
            lines[i] = '|' + '|'.join(parts) + '|\n'
    return ''.join(lines)


class Headings(HTMLParser):
    def __init__(self, body: str):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.current = None
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        if re.fullmatch(r"h[1-6]", tag):
            self.current = {"level": int(tag[1]), "id": dict(attrs).get("id"), "text": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if self.current is not None and tag == "h" + str(self.current["level"]):
            self.items.append(self.current)
            self.current = None


def github_slug(text: str) -> str:
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def add_source_anchors(body: str, original_html: str) -> str:
    original = Headings(original_html).items
    title = None
    if original and original[0]["level"] == 1:
        title = original[0]
        original = original[1:]
    translated = Headings(body).items
    if [h["level"] for h in original] != [h["level"] for h in translated]:
        raise ValueError("원문과 번역의 렌더링된 제목 구조가 다르다")
    used = {h["id"]: h["id"] for h in translated}
    title_ids = list(dict.fromkeys([github_slug(title['text']), title['id']])) if title else []
    title_ids = [x for x in title_ids if x]
    if any(x in used for x in title_ids):
        raise ValueError('원문 제목 앵커가 번역 절과 충돌한다')
    used.update({x: '__title__' for x in title_ids})
    seen = {github_slug(title['text'])} if title else set()
    aliases = {}
    for src, dst in zip(original, translated):
        base = github_slug(src["text"])
        slug = base
        n = 0
        while slug in seen:
            n += 1
            slug = f"{base}-{n}"
        seen.add(slug)
        for candidate in (slug, src["id"]):
            if candidate in used and used[candidate] != dst['id']:
                raise ValueError(f'원문 절 앵커가 다른 번역 절과 충돌한다: {candidate}')
            if candidate and candidate not in used:
                aliases.setdefault(dst["id"], []).append(candidate)
                used[candidate] = dst['id']
    def insert(m):
        spans = "".join(f'<span class="source-anchor" id="{html.escape(a, quote=True)}"></span>'
                        for a in aliases.get(html.unescape(m[2]), []))
        return spans + m[0]
    prefix = ''.join(f'<span class="source-anchor" id="{html.escape(a, quote=True)}"></span>' for a in title_ids)
    return prefix + re.sub(r'<h([1-6])\s+id="([^"]+)"[^>]*>', insert, body)


def rewrite_links(body: str, source_path: str, output_path: str, paths: dict[str, str], commit: str) -> str:
    """위키 문서는 번역본으로, 위키 밖 근거는 고정한 원본 리비전으로 연결한다."""
    def rewrite(m):
        raw = html.unescape(m[1])
        url = urlsplit(raw)
        if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
            return m[0]
        target = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), unquote(url.path)))
        if target in paths:
            path = posixpath.relpath(paths[target], posixpath.dirname(output_path) or ".")
        elif target.startswith("../"):
            return m[0]
        else:
            path = "https://github.com/banatic/acww-decomp/blob/" + quote(commit, safe="") + "/" + quote(target, safe="/")
        if url.query:
            path += "?" + url.query
        if url.fragment:
            path += "#" + url.fragment
        return 'href="' + html.escape(path, quote=True) + '"'
    return re.sub(r'href="([^"]+)"', rewrite, body)


class CitationFolder(HTMLParser):
    """HTML 속성·코드 안의 대괄호를 출처 종료로 오인하지 않는다."""
    prefix = re.compile(r"\[([SEOHPM](?:\s*[+/]\s*[SEOHPM])*)\s*:\s*")

    def __init__(self, grade_info):
        super().__init__(convert_charrefs=False)
        self.grade_info = grade_info
        self.out = []
        self.pending = None
        self.grades = ""
        self.code_depth = 0
        self.pre_depth = 0
        self.brackets = 0

    def emit(self, text):
        (self.pending if self.pending is not None else self.out).append(text)

    def flush_unclosed(self):
        if self.pending is not None:
            self.out.append("[" + self.grades + ": " + "".join(self.pending))
            self.pending = None

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "td", "th", "li", "pre"):
            self.flush_unclosed()
        self.emit(self.get_starttag_text())
        if tag == "code":
            self.code_depth += 1
        if tag == "pre":
            self.pre_depth += 1

    def handle_startendtag(self, tag, attrs):
        self.emit(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in ("p", "td", "th", "li", "pre"):
            self.flush_unclosed()
        self.emit(f"</{tag}>")
        if tag == "code":
            self.code_depth = max(0, self.code_depth - 1)
        if tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)

    def handle_data(self, data):
        if self.code_depth or self.pre_depth:
            self.emit(data)
            return
        i = 0
        while i < len(data):
            if self.pending is None:
                m = self.prefix.search(data, i)
                if not m:
                    self.out.append(data[i:])
                    return
                self.out.append(data[i:m.start()])
                self.grades = re.sub(r"\s+", "", m[1])
                self.pending = []
                self.brackets = 0
                i = m.end()
            else:
                c = data[i]
                if c == "[":
                    self.brackets += 1
                elif c == "]":
                    if self.brackets:
                        self.brackets -= 1
                    else:
                        badges = []
                        for token in re.split(r"([+/])", self.grades):
                            if token in ("+", "/"):
                                badges.append(f'<span class="cite-separator">{token}</span>')
                            else:
                                badges.append(f'<b class="g g-{token}" title="{self.grade_info[token][0]}">{token}</b>')
                        self.out.append(f'<span class="cite" data-grade="{self.grades}"><span class="cite-badge">'
                                        + "".join(badges) + '</span><span class="cite-body">'
                                        + "".join(self.pending) + '</span></span>')
                        self.pending = None
                        i += 1
                        continue
                self.emit(c)
                i += 1

    def handle_entityref(self, name):
        self.emit("&" + name + ";")

    def handle_charref(self, name):
        self.emit("&#" + name + ";")

    def handle_comment(self, data):
        self.emit("<!--" + data + "-->")

    def render(self, body):
        self.feed(body)
        self.close()
        self.flush_unclosed()
        return "".join(self.out)
