"""빌드 완성본을 jsDelivr(서울)로 내보내는 후처리.

사용: python publish.py <사이트 이름> <build/web 경로>
1) 앱 본체(main.dart.<해시>.js)와 assets/ 를 <사이트>/<버전>/ 에 복사
   버전 = 앱 본체 + assets 전체 내용 해시 - 사진만 바뀌어도 새 버전
2) 이 리포에 커밋·push, 커밋 SHA 로 jsDelivr 주소 고정 (불변 캐시)
3) build/web/flutter_bootstrap.js 의 CDN 자리 표시를 그 주소로 채움
   주소가 응답하지 않으면 bootstrap 이 사이트 서버 파일로 대체 로드
"""

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = "master8891/develof-static"
MARK = 'const CDN = "";'


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=HERE, check=True, capture_output=True, text=True).stdout.strip()


KEEP = 2  # 사이트마다 남기는 버전 수 - 새 버전 + 지금 열려 있는 화면이 쓰는 직전 버전


def prune(current: dict[str, str]) -> int:
    """모든 사이트에서 최근 KEEP 개 버전만 남기고 git rm. 옛 주소는 커밋 SHA 로 고정돼 계속 응답"""
    removed = 0
    for site_dir in sorted(p for p in HERE.iterdir() if p.is_dir() and not p.name.startswith(".")):
        vers = [d.name for d in site_dir.iterdir() if d.is_dir()]
        if not vers:
            continue

        def added(name: str, s: str = site_dir.name) -> int:
            if current.get(s) == name:
                return 1 << 62  # 이번에 올린 버전이 가장 최근
            return int(git("log", "-1", "--format=%ct", "--", f"{s}/{name}") or 0)

        vers.sort(key=added, reverse=True)
        for old in vers[KEEP:]:
            git("rm", "-r", "-q", f"{site_dir.name}/{old}")
            removed += 1
    return removed


def main() -> None:
    site, web = sys.argv[1], Path(sys.argv[2]).resolve()
    boot_path = web / "flutter_bootstrap.js"
    boot = boot_path.read_text(encoding="utf-8")
    if MARK not in boot:
        raise SystemExit("flutter_bootstrap.js 에 CDN 자리 표시 누락")
    js = re.search(r"main\.dart\.[0-9a-f]+\.js", boot)
    if not js:
        raise SystemExit("해시 이름 main.dart.js 누락 - hash_bust 먼저 실행")
    h = hashlib.md5((web / js.group(0)).read_bytes())
    for f in sorted((web / "assets").rglob("*")):
        if f.is_file():
            h.update(f.relative_to(web).as_posix().encode())
            h.update(f.read_bytes())
    ver = h.hexdigest()[:12]
    dest = HERE / site / ver
    if not dest.exists():
        dest.mkdir(parents=True)
        shutil.copyfile(web / js.group(0), dest / js.group(0))
        shutil.copytree(web / "assets", dest / "assets")
        git("add", f"{site}/{ver}")
    pruned = prune({site: ver})
    if git("diff", "--cached", "--name-only"):
        git("commit", "-q", "-m", f"{site} {ver}" + (f" (지난 버전 {pruned}개 정리)" if pruned else ""))
        git("push", "-q", "origin", "HEAD")
    # 정리까지 끝난 커밋 - jsDelivr 는 커밋 전체 크기가 50MB 를 넘으면 처음 요청되는 파일을 403 으로 거부
    sha = git("rev-parse", "HEAD")
    cdn = f"https://cdn.jsdelivr.net/gh/{REPO}@{sha}/{site}/{ver}/"
    boot_path.write_text(boot.replace(MARK, f'const CDN = "{cdn}";'), encoding="utf-8", newline="\n")
    print(cdn)


if __name__ == "__main__":
    main()
