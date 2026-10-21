@AGENTS.md

# PM yarn

마브렉스 FE 프로젝트. **기획자가 직접 UI를 만드는 레포**다. 사용자가 비개발자일 수 있다고 가정하고 행동한다.

이 레포에 `TEMPLATE.md` 가 있으면 템플릿 원본이다 — 원본은 템플릿 담당 개발자만 고치고, 기획자는 여기서 복사한 프로젝트 레포에서 작업한다. `TEMPLATE.md` 를 먼저 읽는다.

## 사용자를 대하는 방식

- 에러 로그를 그대로 붙여넣지 마라. 화면 기준으로 설명한다 — "타입 에러" 가 아니라 "이 값이 비어 있을 수 있어서 화면이 깨질 수 있다".
- 무엇을 했는지가 아니라 **화면이 어떻게 달라지는지**를 말한다.
- 막히면 조용히 우회하지 말고 무엇에 막혔는지 말한다.

## 할 수 있는 것

- `src/pages/` 아래 화면 만들기·고치기 — 레이아웃, 스타일, 문구
- 새 페이지 추가 — `src/pages/<이름>.tsx` 신규 + `app/<경로>/page.tsx` 에 re-export 한 줄
- 화면에 쓸 mock 데이터 만들기

## 할 수 없는 것 — 요청받으면 수행하지 말고 알린다

- **API 연동** — `src/shared/api/` 는 FE개발자 영역이다. 데이터가 필요하면 mock 을 만든다.
- **설정 변경** — `eslint.config.mjs`·`tsconfig.json`·`next.config.ts`·`scripts/`·`.claude/`·`.husky/`
- **원장 직접 편집** — `DESIGN.md` 와 `src/app/global.css` 는 잠겨 있다(아래 참조)
- **검증 우회** — `git commit --no-verify` 는 금지다. 게이트에 막히면 코드를 고친다.

이 영역들은 `permissions` 로도 막혀 있다. 막히고 나서 우회를 시도하는 것보다 먼저 말하는 편이 낫다.

## 디자인 시스템

- **UI 작업 전 반드시 `DESIGN.md` 를 읽어라.** 값 충돌 시 DESIGN.md 의 MUST/MUST NOT 이 우선한다.
- **카드·버튼·태그를 만든다면 `SHARED-COMPONENTS.md` 도 읽어라.** 원장이 둘이다 — `DESIGN.md` 가 토큰을 정하고, `SHARED-COMPONENTS.md` 가 그 토큰으로 무엇을 조립하는지 정한다.
- 색·radius·그림자·타이포·모션·여백은 **원장 토큰만** 쓴다. 임의 hex·px·`bg-[#...]`·`p-[13px]`·`[padding:13px]` 같은 임의 속성 문법·리터럴 인라인 `style={{...}}` 는 게이트가 막는다. 단 `style={변수}`(객체를 변수에 담아 넘기는 형태)는 게이트가 보지 못한다 — 리터럴 `style={{` 만 잡는다. `src/app/global.css` 외의 두 번째 `.css` 파일도 막는다(그 파일은 게이트가 검사하지 못하므로 존재 자체를 금지한다).
- 타이포는 `.typo-*` 8클래스(`typo-headline`·`typo-subhead`·`typo-body-head`·`typo-body-large`·`typo-body`·`typo-body-small`·`typo-label`·`typo-label-small`)만 쓴다.
- 색·모양은 Tailwind 유틸리티로 쓴다 — `bg-accent`, `text-text-subtle`, `rounded-pill`, `shadow-extruded`.
- **`origin: brandbook` 값은 마브렉스 공통이라 고정이다.** 바꾸자고 제안하지 마라. `product`·`derived` 값은 프로젝트가 바꿀 수 있지만 원장은 잠겨 있으므로 역시 아래 절차를 따른다.
- **순수 화이트·검정은 팔레트에 없다.** 밝은 면은 `bg-background`, 어두운 면은 `bg-surface-black`.
- 여백은 `p-1`·`p-1.5`·`p-2`·`p-3`·`p-4`·`p-6`·`p-8`·`p-12`·`p-16` 만 쓴다(= 원장 9단). `p-0`·`p-auto`·`p-px` 도 통과한다(레이아웃용으로 별도 허용).
- 모션은 `duration-(--duration-fast)`·`duration-(--duration-standard)`·`ease-standard`. `duration-200` 같은 Tailwind 기본값 금지. `prefers-reduced-motion` 을 존중한다(`motion-safe:`/`motion-reduce:`).

### 원장에 없는 값이 필요할 때

1. **먼저 확정층에서 대안을 제시한다.** "안내 배지엔 `text-subtle` 이 어떨까요" 처럼 묻는다.
2. 사용자가 그래도 새 값이 필요하다고 하면 `DESIGN.proposed.yaml` 에 등록하고 진행한다. `value`·`added`·`by`·`rationale`·`status: pending` 다섯 필드가 모두 필요하다.
3. 등록한 색은 `src/app/global.css` 의 `@theme` 에도 `--color-<이름>` 으로 추가해야 코드에서 쓸 수 있다. 그 파일은 잠겨 있으므로 **사용자에게 요청한다.**

**값을 지어내지 마라.** 원장에 없으면 묻는다.

## 화면 만드는 절차

1. `src/pages/<이름>.tsx` 에 화면을 만든다. 로직·상태·전용 컴포넌트를 그 안에 직접 소유한다.
2. `app/<경로>/page.tsx` 에 re-export 한 줄만 쓴다 — `export { XPage as default } from '@pages/x';`. 여기에 로직을 넣지 않는다.
3. 데이터는 mock 을 쓰는 page 안에 둔다. 두 page 가 같은 mock 을 쓰게 되면 그때 `shared` 로 올린다.

## 같은 것이 두 번째로 나올 때 — 맞출 때·복사할 때·컴포넌트로 뺄 때

**이 절은 "컴포넌트를 만들자" 고 생각할 때만 해당하는 게 아니다.** 아래 요청은 전부 여기에 해당한다.

- "두 화면 카드 모양이 다른데 똑같이 맞춰줘"
- "이거 저 화면에 있는 거랑 같게 해줘"
- 다른 화면의 클래스 묶음·상수를 그대로 가져다 쓰게 될 때

중복은 컴포넌트를 만들 때가 아니라 **맞추고 복사할 때** 생긴다. 복사하기 전에 아래를 본다.

- **처음부터 `src/shared/ui/` 에 넣지 않는다.** 쓰는 화면 안에 만든다. 실제 재사용이 생기기 전에 올리지 않는다.
- 기획자에게 물을 것은 하나다 — **"이거 다른 화면에서도 쓸 것 같나요?"**
  "공용으로 올릴까요" 라고 묻지 마라. 어디에 둘지는 아키텍처 판단이고 기획자의 몫이 아니다.
- 화면마다 후보가 여럿 나온다. 컴포넌트마다 묻지 말고 **화면을 다 만든 뒤 한 번에 묶어서** 묻는다.
- 답이 예이고 실제로 두 번째 사용처가 생겼으면 위치를 정한다.
  - **props 만으로 렌더링이 끝나는 표면·요소** → `src/shared/ui/`
  - **도메인 타입(`Product` 등)을 받는 것** → `src/shared/ui/` 에 두지 않는다. 화면 안에 두고 `src/shared/ui/` 의 컴포넌트를 감싸 쓴다
- `src/shared/ui/` 로 올린 것만 `SHARED-COMPONENTS.md` 에 정의를 등록하자고 **알린다.** 등록은 선택이다 — 기획자가 원하지 않으면 올리기만 한다.

## 카드·버튼·태그를 만들 때

**`SHARED-COMPONENTS.md` 를 먼저 읽어라.** 이 셋은 원장에 레시피가 정해져 있다 — 어떤 색·모서리·여백·모션을 쓰는지, 무엇을 하면 안 되는지. 클래스 묶음을 새로 지어내지 말고 그 레시피대로 조립한다.

거기 없는 컴포넌트는 화면 안에서 만든다. 만들고 나서 등록할지는 위 절을 따른다.

자주 걸리는 것 셋만 여기 적어둔다.

- **`shadow-extruded` 는 눌리는 것의 물성이다**(`DESIGN.md` §6). 누를 수 없는 배너·안내 박스에 정적으로 달지 마라.
- **모션 크기는 원장 변수를 직접 참조한다** — `translate-y-(--hover-lift)`. 여백 스케일로 같은 크기를 재현하는 것(`translate-y-1.25`)은 원장이 MUST NOT 으로 막고 게이트도 잡는다.
- **표면을 통째로 `<button>` 으로 만들지 마라.** `<button>` 은 `<p>`·`<div>` 를 담을 수 없다. 표면은 `div` 로 두고 그 안의 요소가 눌리게 한다.

## 명령어

- `npm run dev` — 개발 서버. 화면을 눈으로 확인한다.
- `npm run lint` — 코드 규칙 게이트. ESLint 규칙 전체를 강제한다(레이어 import 방향·entrypoint 등). **UI 작업 후 필수.**
- `npm run check:tokens` — 원장(DESIGN.md)↔@theme(global.css)↔코드 토큰 게이트. **UI 작업 후 필수.**
- `npm run verify` — 위 둘 + 타입체크. 턴 종료와 `git push` 때 자동으로 돈다.
- `git commit` 때는 이 중 `lint`·`check:tokens` 만 자동으로 돈다 — 타입 에러가 있어도 커밋 자체는 통과할 수 있다.

훅이 자동으로도 돌지만, 막혔을 때 직접 실행해 메시지를 읽는 편이 빠르다.
