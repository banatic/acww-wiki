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
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SNAP = ROOT / "source"
LIVE = Path(r"C:\Users\moomin\Desktop\acww\wiki")
CONTENT = ROOT / "content"

# 원문 경로 -> 번역 경로 (기본은 동일 경로)
RENAMES = {"README.md": "about.md", "STYLE.md": "style.md"}


def content_path(rel: str) -> Path:
    return CONTENT / RENAMES.get(rel, rel)


def md_files(base: Path) -> dict[str, str]:
    return {p.relative_to(base).as_posix(): p.read_text(encoding="utf-8") for p in base.rglob("*.md")}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if not LIVE.exists():
        print(f"원본 위키를 찾을 수 없다: {LIVE}")
        return 1
    snap, live = md_files(SNAP), md_files(LIVE)
    added = sorted(set(live) - set(snap))
    removed = sorted(set(snap) - set(live))
    changed = sorted(k for k in set(snap) & set(live) if snap[k] != live[k])

    if "--accept" in sys.argv:
        for k in removed:
            (SNAP / k).unlink()
        for k in added + changed:
            dst = SNAP / k
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(live[k], encoding="utf-8")
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=LIVE.parent, text=True).strip()
            date = subprocess.check_output(["git", "log", "-1", "--format=%cI"], cwd=LIVE.parent, text=True).strip()
            (SNAP / "SNAPSHOT.txt").write_text(f"commit={commit}\ndate={date}\n", encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            print("git 정보를 읽지 못했다:", e)
        print(f"스냅샷 갱신: 추가 {len(added)}, 변경 {len(changed)}, 삭제 {len(removed)}")
        return 0

    if not (added or removed or changed):
        print("원본과 스냅샷이 같다. 다시 번역할 파일이 없다.")
        return 0
    for k in added:
        print(f"[추가]  {k}  ->  {content_path(k).relative_to(ROOT)}  (새로 번역)")
    for k in removed:
        print(f"[삭제]  {k}  ->  {content_path(k).relative_to(ROOT)}  (번역본도 지울지 결정)")
    for k in changed:
        a, b = snap[k].splitlines(), live[k].splitlines()
        plus = minus = 0
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                plus += 1
            elif line.startswith("-") and not line.startswith("---"):
                minus += 1
        print(f"[변경]  {k}  (+{plus} -{minus})  ->  {content_path(k).relative_to(ROOT)}")
        if "--diff" in sys.argv:
            print("\n".join(difflib.unified_diff(a, b, f"snapshot/{k}", f"live/{k}", lineterm="", n=2)))
            print()
    print(f"\n합계: 추가 {len(added)}, 변경 {len(changed)}, 삭제 {len(removed)}."
          f"  번역을 반영한 뒤  python sync.py --accept  로 스냅샷을 갱신한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
