# PM pnpm

마브렉스 FE 프로젝트 레포. **기획자가 Claude Code 와 대화하며 직접 화면(`src/pages/*.tsx`)을 만들고**, FE개발자가 그 위에 데이터 연동과 공용 로직을 얹는다. 디자인 원장(`DESIGN.md` + `src/app/global.css`)과 자동 게이트(`npm run check:tokens`, 레이어 규칙 `eslint`)가 기획자가 만든 화면이 브랜드 시스템과 아키텍처를 벗어나지 않도록 강제한다. 에이전트에게 적용되는 상세 규칙(할 수 있는 것/없는 것, 디자인 시스템 사용법)은 [`CLAUDE.md`](./CLAUDE.md) 에 있다 — 이 문서는 사람이 레포를 켜고 쓰는 법을 다룬다.

> 이 레포에 `TEMPLATE.md` 가 있으면 템플릿 원본이다 — 화면을 만드는 곳이 아니다. [`TEMPLATE.md`](./TEMPLATE.md) 를 먼저 읽는다. 새 프로젝트를 시작하는 절차도 거기 있다.

## 기획자용

### 먼저 — 어디서 작업할지 고른다

경로는 둘이다. 둘 다 **내 컴퓨터에서 돌기 때문에** Node·Python·Git 이 필요하다.

| 경로 | 설치할 것 |
| --- | --- |
| **Claude Code 데스크톱 앱** | 앱 + Node·Python·Git |
| **터미널** | Claude Code CLI + Node·Python·Git |

둘 다 훅·게이트가 실제로 도는 것을 확인했다. 어느 쪽을 골라도 된다 — 터미널이 익숙하지 않으면 앱이 편하다.

> **웹(claude.ai/code)은 아직 확인하지 않았다.** 웹에서 훅·게이트가 실제로 도는지 재보지 않았다. 확인 전까지는 위 두 경로를 쓴다.

### 설치

셋 다 있어야 한다. **하나라도 없으면 나중에 엉뚱한 데서 막힌다** — 특히 Python 이 없으면 화면은 잘 만들어지는데 저장(커밋)만 안 되고, 뜨는 메시지가 디자인과 아무 상관없어서 원인을 짚기 어렵다.

| | 왜 필요한가 | 확인 |
| --- | --- | --- |
| **Node.js 20.9 이상** | 화면을 띄우고 빌드한다 | `node -v` |
| **Python 3.8 이상** | 디자인 토큰 게이트(`check:tokens`)가 파이썬 스크립트다 | `python3 -V` (Windows 는 `python --version`) |
| **Git** | 작업 저장·공유 | `git --version` |

여기에 더해 **터미널로 쓸 거라면** Claude Code CLI 를(`claude --version`), **앱으로 쓸 거라면** Claude Code 데스크톱 앱을 설치한다.

**macOS**

```bash
brew install node                      # 또는 nodejs.org 설치 파일
xcode-select --install                 # Python 3·Git 포함. 이미 있으면 "already installed"
npm install -g @anthropic-ai/claude-code   # 터미널로 쓸 때만
```

확인:

```bash
node -v && python3 -V && git --version
```

**Windows**

```powershell
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.12      # 설치 중 "Add python.exe to PATH" 를 반드시 체크
winget install Git.Git
npm install -g @anthropic-ai/claude-code   # 터미널로 쓸 때만
```

확인 (PowerShell):

```powershell
node -v; python --version; git --version
```

> **Windows 는 `python3` 가 아니라 `python` 이다.** 이름이 무엇이든 레포가 알아서 찾으므로(`python3`·`python`·`py -3` 순으로 시도한다) 신경 쓸 필요는 없다. 다만 **설치 중 "Add python.exe to PATH" 를 체크하지 않으면** 찾지 못한다 — 그때는 커밋할 때 무엇을 설치해야 하는지 알려주는 메시지가 뜬다.

**세 줄이 다 버전을 뱉으면 준비 끝이다.** 하나라도 `command not found` 가 나오면 그것부터 설치한다.

### 레포 열기

- **데스크톱 앱** — 앱에서 이 레포를 프로젝트로 연다.
- **터미널** — 레포를 클론하고 `npm install` 한 다음, 레포 루트에서 `claude` 를 실행한다.

`npm install` 은 화면을 띄우는 데 필요한 것들과 함께 **커밋 시점 검사(git 훅)까지 자동으로 설치한다.** 프로젝트가 다른 패키지 매니저를 쓰면(`package.json` 의 `packageManager`) 설치만 그 매니저로 한다(`pnpm install`·`yarn install`). 그 밖의 명령(`npm run dev` 등)은 그대로 쓴다.

그리고 **처음 한 번만** 플러그인을 설치한다. 레포가 아키텍처 규칙 플러그인을 쓰는데, 어디서 받을지는 레포에 적혀 있지만 설치는 자동으로 되지 않는다.

```bash
claude plugin install frontend@marblex-plugins
```

Claude Code 를 처음 켤 때 "설치되지 않았다" 며 이 명령을 직접 알려주기도 한다. 안 해도 화면은 만들어지고 규칙 위반은 `npm run lint` 가 그대로 막는다 — 다만 에이전트가 파일 배치를 판단할 때 참고할 안내가 없어진다.

어느 쪽이든 대화창에 원하는 화면을 그대로 적으면 된다. 예: "상품 목록 화면 만들어줘. 카드 3개에 이름이랑 가격 보여주면 돼."

### 화면 하나 만들어보기

요청하면 에이전트가 파일 두 개만 만든다(그 이상이 나오면 의심한다).

- `src/pages/<이름>.tsx` — 화면의 실제 내용. 레이아웃·문구·mock 데이터가 여기 산다.
- `app/<경로>/page.tsx` — re-export 한 줄만 있다. `export { XPage as default } from '@pages/x';`

`app/page.tsx` 는 이미 이 한 줄짜리 형태다(`export { HomePage as default } from '@pages/home';`). **`app/page.tsx` 를 직접 고치라는 안내를 어디서 보든 그건 이 레포에 맞지 않다** — 화면 내용은 항상 `src/pages/` 쪽에서 고친다.

### 만든 화면 보기

```bash
npm run dev
```

브라우저에서 **http://localhost:3000** 을 연다. 켜 둔 채로 두면 화면을 고칠 때마다 자동으로 새로고침되므로, 작업하는 내내 띄워 놓는 편이 편하다. 끌 때는 그 터미널에서 `Ctrl+C`.

새로 만든 화면은 `app/<경로>/page.tsx` 의 경로로 들어간다 — 예를 들어 `app/products/page.tsx` 를 만들었으면 http://localhost:3000/products 다.

에이전트에게 "화면 띄워줘" 라고 해도 된다. 다만 **눈으로 보는 것은 사람이 해야 한다** — 게이트는 원장 밖 값만 막고 "보기 좋은지" 는 보지 못한다.

### 참조 화면은 없다

[`src/pages/home.tsx`](./src/pages/home.tsx) 는 자리만 잡아 둔 보일러플레이트다. 베낄 예시로 쓰지 않는다.

원장 토큰을 실제로 쓰는 참조 화면이 한동안 있었으나 지웠다. 그 화면의 목적은 원장이 브라우저에서 원장 값대로 그려지는지 재는 것이었고, 검증이 끝난 뒤에는 **잘못 베낄 표면**으로만 남았다 — 실제로 그 화면이 원장을 어기고 있던 것을 에이전트가 그대로 복제한 일이 있었다. 측정 결과는 [`docs/ledger-verification.md`](./docs/ledger-verification.md) 에 있다.

쓸 수 있는 값은 [`DESIGN.md`](./DESIGN.md) 에, 화면 만드는 절차는 [`CLAUDE.md`](./CLAUDE.md) 에 있다. 에이전트가 그 둘을 읽고 만들며, 원장 밖 값은 게이트가 막는다.

### 카드·버튼·태그는 이미 정해져 있다

베낄 화면은 없지만 **레시피는 있다.** [`SHARED-COMPONENTS.md`](./SHARED-COMPONENTS.md) 가 Card·Button·Tag 의 색·모서리·여백·눌림 물성을 정해 놓았다. "상품 카드 만들어줘" 라고 하면 에이전트가 그 레시피대로 조립한다.

기획자가 이 파일을 읽을 필요는 없다. 다만 알아두면 좋은 것 둘이 있다.

- **버튼에는 3단 위계가 있다** — 최강조(extruded) · 표준 CTA(outlined) · 일반(solid). 최강조는 화면당 하나다. "이 버튼 더 눈에 띄게 해줘" 라고 하면 에이전트가 이 위계 안에서 올린다.
- **거기 없는 컴포넌트는 화면 안에서 만든다.** 두 번째 화면에서 또 쓰게 되면 그때 공용으로 올릴지 물어본다.

### 막혔을 때

- **"원장에 없는 색이다" 같은 메시지가 뜬다** — 임의 hex 값이나 새 Tailwind 색 유틸리티는 게이트가 막는다. 에이전트가 확정층에서 가장 가까운 대안을 먼저 제안해야 한다. 그래도 새 값이 꼭 필요하면 에이전트가 `DESIGN.proposed.yaml` 에 근거와 함께 등록하고 진행한다.
- **"이건 FE개발자 영역이다" 라는 답을 받는다** — API 연동(`src/shared/api/`)이나 설정 변경은 에이전트가 하지 않는다. FE개발자에게 요청한다.
- **원장 파일(`DESIGN.md`, `src/app/global.css`)이나 설정(`scripts/`, `.claude/`, `.husky/`)을 직접 고쳐야 하는 상황** — 에이전트는 이 영역을 고치지 못한다(막혀 있다). [`docs/maintenance.md`](./docs/maintenance.md) 에 사람이 직접 고치는 절차가 있다. FE개발자나 디자이너에게 전달한다.

## FE개발자용

### 구조

- `app/` — Next.js App Router. 라우팅 전용이다. 각 `page.tsx` 는 `src/pages/` 를 re-export 하는 한 줄로만 존재하고 로직을 두지 않는다.
- `src/` — 레이어드 구조. 현재 실제로 쓰는 레이어는 `app`(전역 provider 등) · `pages`(화면) · `shared`(공용 `api`/`config`/`routes`) 세 개다. `widgets`·`features`·`entities` alias(`tsconfig.json` 의 `@widgets`·`@features`·`@entities`)는 잡혀 있지만 아직 그 디렉터리는 없다 — 필요해지면 만든다.
- 레이어 import 방향(`shared → pages → app` 한 방향, entrypoint 우회 금지, 파일명 kebab-case)은 `eslint.config.mjs` 가 강제한다.
- 루트의 `pages/`(빈 폴더, `pages/README.md` 참고)와 `src/pages/`(실제 화면 레이어)를 혼동하지 않는다 — 루트 `pages/` 는 Next.js 가 Pages Router 로 폴백하는 것만 막는 용도로 비워 둔다.

### 원장과 게이트

- 토큰 단일 원장은 `DESIGN.md`(frontmatter) + `src/app/global.css`(`@theme`) 두 곳이다. 둘이 어긋나면 게이트가 막는다.
- [`SHARED-COMPONENTS.md`](./SHARED-COMPONENTS.md) 는 **컴포넌트 원장**이다. `DESIGN.md` 가 토큰을 정하고 이쪽이 그 토큰으로 무엇을 조립하는지를 정한다. 값은 전부 `{colors.accent}` 같은 토큰 참조이며 리터럴을 쓰지 않는다 — 규칙마다 피그마 노드나 `DESIGN.md` § 를 근거로 단다.
- `DESIGN.proposed.yaml` 은 승격 대기 토큰 제안층이다.
- `DESIGN.md` 의 값에는 출처(`origin`)가 붙는다. `colors` 는 토큰마다, 나머지는 블록마다다. `brandbook` 은 마브렉스 공통·고정이고 `product`·`derived` 는 프로젝트가 바꿀 수 있다. 출처가 없는 블록은 게이트가 막는다.
- `npm run check:tokens`(`scripts/check-design-tokens.py`)가 확정층 · 제안층 · `@theme` · 앱 코드 네 곳을 대조한다.
- 두 원장 파일을 사람이 직접 고쳐야 하는 경우(토큰 승격, 반려, 확정층 값 변경)의 절차는 [`docs/maintenance.md`](./docs/maintenance.md) 에 있다.

### 훅 구성

| 시점 | 실행 | 비고 |
| --- | --- | --- |
| Claude Code 턴 종료(`Stop`) | `npm run verify` | lint + typecheck + check:tokens. 실패하면 그 턴이 끝나지 않고 에이전트가 이어서 고친다(재진입 시에도 여전히 실패하면 그때는 보고만 하고 턴을 끝낸다) — `.claude/hooks/verify-on-stop.sh`. |
| Claude Code 편집 직후(`PostToolUse`, 보너스 층) | `npm run check:tokens` | 빠른 피드백용. 여기 의존하지 않는다 — 실질 보장은 Stop 훅과 아래 git 훅이 진다 — `.claude/hooks/quick-check.sh`. |
| `git commit`(husky `pre-commit`) | `npm run lint && npm run check:tokens` | 타입체크는 여기 없다 — 타입 에러가 있어도 커밋 자체는 통과할 수 있다. |
| `git push`(husky `pre-push`) | `npm run verify` | lint + typecheck + check:tokens 전체. |
| GitHub PR·`main` push(GitHub Actions) | `npm run verify` | `.github/workflows/verify.yml`. git 훅을 건너뛴 커밋도 여기서 걸린다. 실패한 PR 의 머지까지 막으려면 레포 관리자가 `main` 보호 규칙에서 이 검사를 필수로 지정한다. |

git 훅(`pre-commit`/`pre-push`)은 Claude Code 밖에서도 도는 강제 수단이다 — 로컬 git 훅이라 에디터로 직접 고친 커밋도 같은 훅을 거친다. 다만 이건 절대적인 보장은 아니다: 사람이 터미널에서 직접 `git commit -n`·`HUSKY=0`·`core.hooksPath` 같은 걸로 이 훅 자체를 건너뛸 수 있다(에이전트가 Bash 로 시도하는 쪽은 `.claude/hooks/no-verify-guard.sh` 가 막는다). 그리고 훅이 보는 건 그 시점의 작업 트리이지, 커밋된 내용이 이후에도 그대로 남아 있다는 것까지 보장하지는 않는다. 이 두 구멍은 GitHub Actions 가 커밋된 내용 그대로를 다시 검사해 메운다.

### 명령어

- `npm run dev` / `npm run build` / `npm run start`
- `npm run lint` — ESLint 규칙 전체. 레이어 import 방향·파일명 규칙 등
- `npm run typecheck` — `tsc --noEmit`
- `npm run check:tokens` — 원장 ↔ `@theme` ↔ 코드 토큰 게이트
- `npm run verify` — 위 세 개 전부(lint + typecheck + check:tokens). `Stop` 훅과 `pre-push` 가 이걸 돌린다.

## 잠금 영역

에이전트가 아래 경로를 고치는 것을 막아 놨다(`permissions`). 게이트나 훅이 막히면 코드를 고치는 대신 **그 규칙 자체를 손보는 쪽으로 우회하기 쉬운 영역**이라서다.

| 경로 | 이유 |
| --- | --- |
| `DESIGN.md`, `src/app/global.css` | 디자인 토큰 원장 그 자체. 승격·반려·확정층 값 변경은 디자이너·FE개발자의 판단이 필요하다. |
| `scripts/` | 토큰 게이트 구현. 게이트가 막히면 스캐너를 느슨하게 만드는 쪽으로 우회할 수 있다. |
| `.claude/`, `.husky/` | 훅·권한 설정 자체. 강제 수단을 에이전트 스스로 바꿀 수 없게 한다. |
| `eslint.config.mjs`, `tsconfig.json`, `next.config.ts` | lint 규칙과 빌드 설정. |

`permissions` 의 `deny` 는 Edit/Write 툴 호출만 막는 게 아니다 — `cp`, `echo > file`, `sed -i` 처럼 Bash 로 우회해 같은 파일에 쓰려는 시도도 실측으로 막는다. 세션 안에서는 이 경로도 안전하다는 뜻이다.

이 파일들을 사람이 직접 고쳐야 할 때(토큰 승격, 반려, 확정층 값 변경 등)의 정규 절차는 [`docs/maintenance.md`](./docs/maintenance.md) 에 있다 — `permissions` 는 Claude Code 세션 안에서만 작동하므로, 에이전트를 거치지 않고 직접 편집하는 절차다.
