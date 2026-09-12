#!/usr/bin/env python3
"""원본 위키(acww/wiki) 변경분 점검 도구.

source/ 에는 번역의 기준이 된 원문 스냅샷이 고정(freeze)되어 있다.
이 스크립트는 원본 레포의 현재 wiki/ 와 스냅샷을 비교해, 다시 번역해야 할 파일만 알려 준다.

  python sync.py            변경·추가·삭제된 파일 목록과 diff 요약
  python sync.py --diff     파일별 전체 diff 출력
  python sync.py --accept   원본을 스냅샷으로 복사해 기준을 갱신 (번역 반영 후에 실행)
"""
from __future__ import annotations

import difflib
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
SNAP = ROOT / "source"
LIVE = Path(r"C:\Users\moomin\Desktop\acww\wiki")
CONTENT = ROOT / "content"

# 원문 경로 -> 번역 경로 (기본은 동일 경로)
RENAMES = {"README.md": "about.md", "STYLE.md": "style.md"}


def content_path(rel: str) -> Path:
    return (CONTENT / RENAMES.get(rel, rel)) if rel.endswith('.md') else SNAP/rel


def md_files(base: Path) -> dict[str, str]:
    return {p.relative_to(base).as_posix(): p.read_text(encoding="utf-8") for p in base.rglob('*') if p.suffix in ('.md', '.tsv')}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=LIVE, help='미리 고정한 원문 디렉터리도 지정할 수 있다')
    parser.add_argument('--revision', help='고정 원문의 원본 Git 커밋 (전체 SHA)')
    parser.add_argument('--accept', action='store_true')
    parser.add_argument('--diff', action='store_true')
    args = parser.parse_args()
    incoming = args.source.resolve()
    if not incoming.exists():
        print(f"원본 위키를 찾을 수 없다: {incoming}")
        return 1
    snap, live = md_files(SNAP), md_files(incoming)
    added = sorted(set(live) - set(snap))
    removed = sorted(set(snap) - set(live))
    changed = sorted(k for k in set(snap) & set(live) if snap[k] != live[k])

    if args.accept:
        if incoming != LIVE.resolve() and not args.revision:
            parser.error('고정 원문을 반영할 때는 --revision으로 원본 커밋을 지정한다')
        missing = [k for k in live if k.endswith('.md') and not content_path(k).exists()]
        if missing:
            print('번역이 없는 원문은 기준으로 확정할 수 없다:', ', '.join(missing))
            return 1
        commit = subprocess.check_output(['git', 'rev-parse', args.revision or 'HEAD'], cwd=LIVE.parent, text=True).strip()
        date = subprocess.check_output(['git', 'show', '-s', '--format=%cI', commit], cwd=LIVE.parent, text=True).strip()
        # 커밋 이름만 붙이고 다른 바이트를 확정하는 실수를 막는다.
        tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit, '--', 'wiki'], cwd=LIVE.parent, text=True).splitlines()
        expected = {p.removeprefix('wiki/') for p in tracked if p.endswith(('.md', '.tsv'))}
        if expected != set(live):
            print('고정 원문의 파일 목록이 지정한 커밋과 다르다')
            return 1
        for k, text in live.items():
            result = subprocess.run(['git', 'show', f'{commit}:wiki/{k}'], cwd=LIVE.parent, capture_output=True)
            if result.returncode or result.stdout.decode('utf-8').replace('\r\n', '\n') != text:
                print(f'고정 원문이 지정한 커밋과 다르다: {k}')
                return 1
        for k in removed:
            (SNAP / k).unlink()
        for k in added + changed:
            dst = SNAP / k
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(live[k], encoding="utf-8", newline='\n')
        dirty = []
        manifest = {'commit': commit, 'commit_date': date,
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'working_tree_changes': dirty,
                    'hash_format': 'SHA-256 of UTF-8 text with LF line endings',
                    'files': {k:hashlib.sha256(v.encode('utf-8')).hexdigest() for k,v in sorted(live.items())}}
        (SNAP/'SNAPSHOT.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
        (SNAP/'SNAPSHOT.txt').write_text(f'commit={commit}\ndate={date}\ndirty={len(dirty)}\n', encoding='utf-8', newline='\n')
        print(f"스냅샷 갱신: 추가 {len(added)}, 변경 {len(changed)}, 삭제 {len(removed)}")
        return 0

    if not (added or removed or changed):
        print("원본과 스냅샷이 같다. 다시 번역할 파일이 없다.")
        return 0
    for k in added:
        action = '새로 번역' if k.endswith('.md') else '보조 데이터 고정'
        print(f"[추가]  {k}  ->  {content_path(k).relative_to(ROOT)}  ({action})")
    for k in removed:
        action = '번역본도 지울지 결정' if k.endswith('.md') else '고정 보조 데이터에서 제거'
        print(f"[삭제]  {k}  ->  {content_path(k).relative_to(ROOT)}  ({action})")
    for k in changed:
        a, b = snap[k].splitlines(), live[k].splitlines()
        plus = minus = 0
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                plus += 1
            elif line.startswith("-") and not line.startswith("---"):
                minus += 1
        print(f"[변경]  {k}  (+{plus} -{minus})  ->  {content_path(k).relative_to(ROOT)}")
        if args.diff:
            print("\n".join(difflib.unified_diff(a, b, f"snapshot/{k}", f"live/{k}", lineterm="", n=2)))
            print()
    print(f"\n합계: 추가 {len(added)}, 변경 {len(changed)}, 삭제 {len(removed)}."
          f"  번역을 반영한 뒤  python sync.py --accept  로 스냅샷을 갱신한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
