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
        git("commit", "-q", "-m", f"{site} {ver}")
        git("push", "-q", "origin", "HEAD")
    sha = git("log", "-1", "--format=%H", "--", f"{site}/{ver}")
    cdn = f"https://cdn.jsdelivr.net/gh/{REPO}@{sha}/{site}/{ver}/"
    boot_path.write_text(boot.replace(MARK, f'const CDN = "{cdn}";'), encoding="utf-8", newline="\n")
    print(cdn)


if __name__ == "__main__":
    main()
