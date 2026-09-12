"""원문/번역의 구조·출처와 빌드된 페이지의 내부 링크를 검사한다."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown
from wiki_html import Headings

ROOT = Path(__file__).parent
PREFIX = re.compile(r"\[[SEOHPM](?:\s*[+/]\s*[SEOHPM])*\s*:\s*")


def citations(text):
    """코드의 대괄호와 출처 안의 마크다운 링크를 포함해 태그 전체를 비교한다."""
    tags = []
    pos = 0
    while match := PREFIX.search(text, pos):
        i = match.end()
        depth = 1
        code = ""
        while i < len(text):
            if text[i] == "`":
                run = re.match(r"`+", text[i:])[0]
                if not code:
                    code = run
                elif code == run:
                    code = ""
                i += len(run)
                continue
            if not code:
                if text[i] == "[" and (i == 0 or text[i - 1] != "\\"):
                    depth += 1
                elif text[i] == "]" and (i == 0 or text[i - 1] != "\\"):
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
            i += 1
        if depth:
            # 원문에도 불완전한 태그가 있을 수 있다. 해당 줄 그대로 비교한다.
            i = text.find("\n", match.start())
            if i < 0:
                i = len(text)
        tags.append(re.sub(r"\s+", " ", text[match.start():i]))
        pos = i
    return tags


def structure(text):
    body = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    return ([h['level'] for h in Headings(body).items],
            len(re.findall(r"(?m)^\|", text)))


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag in ('a', 'link') and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag in ('img', 'script') and attrs.get('src'):
            self.links.append(attrs['src'])


def validate_source(source):
    errors = []
    manifest_path = source/'SNAPSHOT.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        info_path = source/'SNAPSHOT.txt'
        info = dict(line.split('=',1) for line in info_path.read_text(encoding='utf-8').splitlines() if '=' in line) if info_path.exists() else {}
        if info.get('commit') != manifest['commit'] or info.get('date') != manifest['commit_date']:
            errors.append('스냅샷 텍스트와 JSON의 커밋 또는 날짜가 다르다')
        actual_hashes = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
                         for p in source.rglob('*') if p.suffix in ('.md', '.tsv')}
        if actual_hashes != manifest['files']:
            errors.append('스냅샷 파일 목록 또는 SHA-256이 기록과 다르다')
    elif source.resolve() == (ROOT/'source').resolve():
        errors.append('스냅샷 해시 기록이 없다')
    expected = set()
    for p in sorted(source.rglob('*.md')):
        rel = p.relative_to(source).as_posix()
        translated = {'README.md':'about.md', 'STYLE.md':'style.md'}.get(rel, rel)
        expected.add(translated)
        target = ROOT / 'content' / translated
        if not target.exists():
            errors.append(f'{translated}: 번역 없음')
            continue
        original = p.read_text(encoding='utf-8')
        korean = target.read_text(encoding='utf-8')
        if f'<!-- source: wiki/{rel} -->' not in korean:
            errors.append(f'{translated}: 원문 경로 주석 없음')
        if structure(original) != structure(korean):
            errors.append(f'{translated}: 제목/표 행 구조 불일치 {structure(original)} -> {structure(korean)}')
        a, b = citations(original), citations(korean)
        if a != b:
            missing = list((Counter(a) - Counter(b)).elements())
            extra = list((Counter(b) - Counter(a)).elements())
            errors.append(f'{translated}: 출처 불일치 원문 {len(a)} / 번역 {len(b)}; 누락 {missing[:2]}; 추가 {extra[:2]}')
    actual = {p.relative_to(ROOT/'content').as_posix() for p in (ROOT/'content').rglob('*.md')}
    for extra in sorted(actual - expected):
        errors.append(f'{extra}: 원문 대응 없음')
    print(f'원문 {len(expected)}편 / 번역 {len(actual)}편 검사')
    return errors


def validate_site():
    base = (ROOT/'docs').resolve()
    pages = {p.resolve():Links(p.read_text(encoding='utf-8')) for p in base.rglob('*.html')}
    errors = []
    for p, doc in pages.items():
        duplicates = [s for s, n in Counter(doc.ids).items() if n > 1]
        if duplicates:
            errors.append(f'{p.relative_to(base)}: 중복 앵커 {duplicates[:5]}')
        for href in doc.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            path = unquote(url.path)
            if path.startswith('/acww-wiki/'):
                dest = base/path.removeprefix('/acww-wiki/')
            elif path.startswith('/'):
                continue
            else:
                dest = p.parent/path if path else p
            dest = dest.resolve()
            if dest.is_dir():
                dest = dest/'index.html'
            if not dest.is_relative_to(base) or not dest.exists():
                errors.append(f'{p.relative_to(base)}: 없는 내부 경로 {href}')
            elif url.fragment and dest in pages and unquote(url.fragment) not in pages[dest].ids:
                errors.append(f'{p.relative_to(base)}: 없는 앵커 {href}')
    index = json.loads((base/'search-index.json').read_text(encoding='utf-8'))
    for item in index:
        url = urlsplit(item['u']); dest=(base/unquote(url.path)).resolve()
        if dest not in pages or (url.fragment and unquote(url.fragment) not in pages[dest].ids):
            errors.append(f'검색 색인: 없는 대상 {item["u"]}')
    print(f'HTML {len(pages)}개 / 검색 항목 {len(index)}개 검사')
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'source')
    parser.add_argument('--site', action='store_true')
    args = parser.parse_args()
    errors = validate_source(args.source)
    if args.site:
        errors += validate_site()
    for error in errors:
        print(error)
    print(f'오류 {len(errors)}건')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
