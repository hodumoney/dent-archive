# 완전 무료 웹사이트 만들기 — GitHub 따라하기

코딩 몰라도 됩니다. 아래 순서대로 클릭만 하면 돼요.
막히면 그 화면을 캡처해서 물어보세요.

---

## 1단계 · GitHub 가입 (무료)
1. https://github.com 접속 → **Sign up**
2. 이메일, 비밀번호, 사용자이름(영문, 예: `hodumoney`) 입력해서 가입
3. 무료 플랜(Free) 선택

## 2단계 · 저장소(repository) 만들기
1. 오른쪽 위 **+** → **New repository**
2. Repository name: 아무거나 (예: `dent-archive`)
3. **Private** 선택 (중요 — 내 것만 보이게)
4. **Create repository** 클릭

## 3단계 · 파일 올리기
1. 방금 만든 저장소 화면에서 **uploading an existing file** 링크 클릭
   (또는 **Add file → Upload files**)
2. `dent-tracker` 압축을 푼 폴더를 열고, **그 안의 파일과 폴더를 전부 선택**해서
   업로드 칸으로 **드래그**합니다.
   - `.github`, `templates` 같은 폴더도 함께 드래그하면 구조가 유지됩니다.
3. 아래 **Commit changes** (초록 버튼) 클릭
4. 파일 목록에 `crawl.py`, `build_site.py`, `.github` 폴더 등이 보이면 성공

> `.github` 폴더가 안 올라갔다면: **Add file → Create new file** →
> 파일명 칸에 `.github/workflows/update.yml` 입력 →
> 안내서와 함께 드린 `update.yml` 내용을 붙여넣고 저장.

## 4단계 · 로그인 정보를 금고(Secrets)에 넣기
비밀번호는 파일이 아니라 안전한 금고에 넣습니다.
1. 저장소 상단 **Settings** → 왼쪽 **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
   - Name: `DENT_ID` / Secret: 게시판 아이디(`twowater95`) → **Add secret**
3. 다시 **New repository secret**
   - Name: `DENT_PW` / Secret: 게시판 비밀번호 → **Add secret**

## 5단계 · 웹사이트 기능(Pages) 켜기
1. **Settings** → 왼쪽 **Pages**
2. **Source** 를 **GitHub Actions** 로 선택

## 6단계 · 처음 한 번 실행하기
1. 저장소 상단 **Actions** 탭
2. (권한 확인 화면이 나오면 초록 버튼으로 활성화)
3. 왼쪽에서 **치과 아카이브 업데이트** 클릭 → 오른쪽 **Run workflow** → 다시 **Run workflow**
4. 잠시 뒤 목록에 실행 항목이 뜨고, 초록 체크(✓)가 되면 성공
   - 빨간 X 가 뜨면, 그 항목을 눌러 로그를 캡처해서 물어보세요.

## 7단계 · 내 사이트 주소 확인
- **Settings → Pages** 위쪽에 나오는 주소가 내 사이트예요.
  (형식: `https://내아이디.github.io/dent-archive/`)
- 이 주소를 휴대폰·PC 어디서든 열면 대시보드가 보입니다.
- 이후로는 하루 4번(한국시간 08·12·16·20시) 자동으로 갱신됩니다.

---

### 자동 실행 시간 바꾸기 (선택)
`.github/workflows/update.yml` 의 `cron` 시간을 바꾸면 됩니다. UTC 기준이라
한국시간에서 9를 뺀 값입니다. (예: 한국 08시 = UTC 23시 → `0 23 * * *`)

### 참고
- 사이트 주소는 검색에 노출되지 않게 해뒀지만, 주소를 아는 사람은 볼 수 있는
  공개 페이지입니다(무료 플랜 특성). 링크 공유에 유의하세요.
- 게시판이 서버(로봇) 접근을 막을 가능성도 있습니다. 6단계에서 빨간 X 가 뜨고
  로그에 로그인 실패가 보이면, 방식을 조정할 수 있으니 알려주세요.
