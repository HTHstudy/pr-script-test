# 원장 검증 기록 — 2026-09-02

`DESIGN.md` 의 토큰과 규칙이 **실제 브라우저에서 원장 값대로 그려지는지** 재서 남긴 기록이다.

## 왜 이 문서가 있나

게이트(`npm run check:tokens`)가 검사하는 것은 **원장 ↔ `@theme` 대조**다. 두 파일의 값이 같은지는 보지만, 그 값이 브라우저에서 의도한 결과를 내는지는 보지 못한다. 이 둘은 다르다 — 실제로 `press-offset` 은 원장과 `@theme` 이 완벽히 일치한 상태에서 코드가 그 값을 **쓸 수 없었다**(아래 참조).

검증은 참조 화면(`src/pages/home.tsx`·`products.tsx`)으로 했다. 그 화면들은 이 검증을 위해 만든 것이고, 검증이 끝나 보일러플레이트로 줄였다. **측정 증거가 화면과 함께 사라지지 않도록 여기 남긴다.**

## 방법

`npm run dev` + Chrome DevTools. `getComputedStyle` 로 실제 계산값을 읽고, 빌드 산출 CSS(`.next/static/chunks/*.css`)에서 컴파일 결과를 확인했다. 원장 값과 한 줄씩 대조했다.

## 타이포그래피 — 8클래스 × 두 브레이크포인트

계산값 전부 원장과 일치했다. `size | weight | lineHeight | tracking | family` 순.

| 클래스 | PC (1500px) | 모바일 (390px) |
| --- | --- | --- |
| `typo-headline` | 28px \| 900 \| 26.6px \| -0.84px \| GT Maru | **22px \| 900 \| 20.9px \| -0.66px** |
| `typo-subhead` | 24px \| 700 \| 23.52px \| -0.72px \| GT Maru | **20px \| 700 \| 19.6px \| -0.6px** |
| `typo-body-head` | 18px \| 700 \| 18.18px \| normal \| GT Maru | 동일 |
| `typo-body-large` | 18px \| 400 \| 23.58px \| normal \| GT Maru | 동일 |
| `typo-body` | 16px \| 400 \| 19.68px \| normal \| Inter | 동일 |
| `typo-body-small` | 14px \| 400 \| 17.36px \| normal \| Inter | 동일 |
| `typo-label` | 14px \| 700 \| 17.36px \| normal \| GT Maru | 동일 |
| `typo-label-small` | 12px \| 500 \| 15.24px \| normal \| GT Maru | 동일 |

행간이 원장의 백분율과 맞는지도 확인했다 — headline 95% × 28px = 26.6px, subhead 98% × 24px = 23.52px, body-head 101% × 18px = 18.18px.

원장에서 `fontSize` 가 `{ pc, mobile }` 인 것은 `headline`·`subhead` 둘뿐이고, 그 둘만 좁은 화면에서 값이 바뀌었다. 나머지 여섯은 단일 값이므로 바뀌지 않는 것이 맞다. 브레이크포인트는 `breakpoints.mobile-max: 768px` 이고 390px 에서 `(max-width: 768px)` 가 매칭됐다.

## 한글 자간 예외 — 발화한다

`hangulTracking` 은 `html[lang='ko']` 에서 `headline`·`subhead` 의 자간을 `-0.06em` 에서 `-0.03em` 으로 푼다. 조용히 안 걸릴 수 있는 종류라 따로 확인했다.

`app/layout.tsx` 가 `<html lang="ko">` 를 준다. 계산값이 headline `-0.84px`(= 28px × -0.03) 로 나왔다 — 예외가 적용된 값이다. 예외가 없었다면 `-1.68px`(× -0.06)이었을 것이다. subhead 도 `-0.72px`(= 24px × -0.03).

## 서체 — 3종 로드 확인

`document.fonts` 에 등록된 것:

```
GT Maru/400 · GT Maru/500 · GT Maru/700 · GT Maru/900
Inter/100 900 (variable) · Inter Fallback
Pretendard Variable/45 920
```

`document.fonts.check('900 1.75rem "GT Maru"')` → `true`. **원장이 쓰는 네 굵기(400·500·700·900)가 전부 있다.** 서체가 없으면 조용히 대체되어 화면은 그려지지만 원장과 다른 결과가 나오는 자리라 확인이 필요했다.

## 모션 — 원장 변수 참조가 컴파일된다

`press-offset` 은 원장·`@theme` 값이 일치했는데도 **코드가 쓸 수 없는 상태였다.** 게이트가 잡지 못하는 종류의 결함이다.

원장이 `press-offset: '4px 5px'` 로 x·y 를 한 변수에 담았고, Tailwind 의 `translate-*` 는 **스칼라 하나를 두 축에 적용하는** 유틸리티다. 컴파일 결과로 확인:

```css
translate-4                 → --tw-translate-x: calc(var(--spacing) * 4);
                              --tw-translate-y: calc(var(--spacing) * 4)
translate-(--press-offset)  → --tw-translate-x: var(--press-offset);
                              --tw-translate-y: var(--press-offset)
                            → translate: 4px 5px 4px 5px   (무효)
```

`translate-4` 도 같은 값을 양쪽에 쓴다. 즉 Tailwind 는 계약대로 동작했고 결함은 스칼라 자리에 값 두 개를 담은 원장에 있었다. 우회로 코드가 `translate-x-1`(4px) / `translate-y-1.25`(5px) 로 값을 **여백 스케일에 재기입**하고 있었고, 그 결과 그림자 오프셋이 `spacing.scale` 기본단위에 묶였다. `1.25` 는 원장 9단 밖 배수이며, 게이트는 `translate-` 를 여백 검사 대상에 두지 않아 잡지 못한다.

축별로 쪼개 고쳤다(`press-offset-x`/`-y`). 고친 뒤 컴파일 결과:

```css
translate-x-(--press-offset-x):active → --tw-translate-x: var(--press-offset-x)   해당 축만
translate-y-(--press-offset-y):active → --tw-translate-y: var(--press-offset-y)
translate-y-(--hover-lift):hover      → --tw-translate-y: var(--hover-lift)
```

브라우저에서 변수가 `4px` / `5px` / `-2px` 로 해석되는 것도 확인했다. `press-offset` 값은 `shadows.extruded` 의 오프셋(`4px 5px 0`)과 같다 — 눌린 표면이 정확히 그림자 자리로 내려앉기 위한 것이므로 두 값은 함께 움직인다.

`hover-lift` 도 같은 결함이었다. 원장 값이 스칼라라 참조는 가능했는데 코드가 `-translate-y-0.5`(= spacing × 0.5)로 우회했다. `0.5` 도 9단 밖이다.

## `prefers-reduced-motion` — MUST 를 지킨다

원장 §6 이 MUST 로 요구한다. 빌드 산출 CSS 에서 모션 규칙이 어느 미디어쿼리에 들어갔는지 확인했다.

```
@media (prefers-reduced-motion: no-preference)   5개
    motion-safe:hover:translate-y-(--hover-lift)
    motion-safe:hover:shadow-extruded
    motion-safe:active:translate-x-(--press-offset-x)
    motion-safe:active:translate-y-(--press-offset-y)
    motion-safe:active:shadow-none
@media (prefers-reduced-motion: reduce)          1개
    motion-reduce:transition-none
```

모션 5규칙이 **전부 `no-preference` 안에만** 있다. 즉 `reduce` 에서는 덮어써지는 것이 아니라 **아예 존재하지 않는다.** transition 도 따로 끊는다.

## 그 외 확인된 것

- **radius 3단** — `rounded-small`(10px) · `rounded-card`(24px) · `rounded-pill` 전부 실제 렌더 확인
- **`shadow-extruded`** — `4px 5px 0 #070707`. hover 시 등장, active 시 소멸
- **`after:absolute after:inset-0` 오버레이** — Tailwind v4 가 `@property --tw-content { initial-value: "" }` 를 내보내므로 `content` 를 따로 주지 않아도 가상요소가 그려진다. 카드 네 귀퉁이·가운데 다섯 지점이 모두 안쪽 버튼으로 히트되는 것을 `elementFromPoint` 로 확인

## 검증하지 않은 것 — 그리고 왜 하지 않아도 되는가

**색 8개** — `surface-dark` · `accent-pressed` · `accent-deep` · `grey-tint` · `scrim` · `warning` · `danger` · `danger-tint` 는 코드에 쓰인 적이 없다.

**`duration-fast`** 도 쓰인 적이 없다(쓰인 것은 `duration-standard`).

스와치 화면을 만들어 렌더를 확인하는 것은 값을 하지 않는다. 게이트가 이미 `--color-<이름>` 이 `@theme` 에 있고 원장 hex 와 같은지 검사하며, **단순 색 유틸리티에는 `press-offset` 같은 조용히 깨지는 경로가 없다.** `press-offset` 검증이 값을 했던 이유는 값 두 개를 스칼라 자리에 담은 구조적 결함이 있었기 때문이고, 색에는 그런 구조가 없다. `duration-fast` 도 스칼라 변수라 검증된 `duration-standard` 와 같은 기제를 탄다.

`scrim`(`#07070799`)은 8자리 hex 다. 게이트가 `#RRGGBBAA` 를 허용하고 브라우저도 지원한다. 실제로 쓰는 순간 따라오는 z-index·backdrop 문제는 원장 검증이 아니라 화면 설계 문제다.

## 발견한 게이트 공백 — 없는 변수 참조가 통과했다 (막았다)

측정 중 발견했다. `duration-(--duration-standard)` 를 `duration-(--duraiton-standard)`(오타)로 바꿔 게이트를 돌렸다.

```
npm run check:tokens → OK
```

Tailwind 는 `var(--duraiton-standard)` 를 그대로 내보내고, 그 변수가 없으므로 **모션이 조용히 걸리지 않는다.** 게이트는 원장 ↔ `@theme` 만 대조하고 코드의 `(--변수)` 참조가 실재하는지는 보지 않았다.

대괄호 임의값(`bg-[#3B82F6]`)과 달리 이 괄호 문법은 원장을 가리키므로 허용해 왔는데, **"가리킨다" 와 "실재한다" 는 다르다.** 그리고 원장 §6 이 이제 모션 값을 변수 직접 참조로 MUST 지정하므로 이 형태의 사용이 늘어난다.

`checks.check_var_refs` 를 추가해 막았다. 코드(`.ts`/`.tsx`/`.js`/`.jsx`)의 `-(--x)` 참조를 모아 `global.css` 선언과 대조하고, 없으면 차단하며 오타에 가까운 이름을 제안한다.

```
src/pages/home.tsx:8: --duraiton-standard 는 @theme 에 선언되지 않았다.
  --duration-standard 를 쓰려던 것인가? 오타가 아닌지 먼저 확인하라 — ...
```

판단 두 가지를 기록한다.

- **`.css` 는 보지 않는다.** 선언부이고 `var(--x)` 사용은 대조 대상이 아니다.
- **Tailwind 내장 변수(`--spacing` 등)도 `global.css` 에 없으면 잡는다.** 오탐이 아니라 의도다 — 원장에 없는 변수를 코드가 가리키는 것이 게이트가 막으려는 드리프트 그 자체다. `p-(--spacing)` 대신 `p-1` 을 쓴다.

단위 테스트 9건을 붙였다(`npm run test:gate`, 119 → 128건).

## 제안층 루프 E2E — 2026-09-03

기획자가 "안내 배지 파란색으로" 를 요구한 상황을 끝까지 재현했다. `DESIGN.proposed.yaml` 이 계속 비어 있어 이 흐름은 한 번도 돌아본 적이 없었다.

| 단계 | 결과 |
| --- | --- |
| 1. 확정층에서 대안 제시 | 정상 — 팔레트에 파란 계열이 0건인 것을 기계로 확인할 수 있다 |
| 2. `DESIGN.proposed.yaml` 등록 | 정상 — 에이전트가 5필드 갖춰 등록, 검증 통과 |
| 3. `global.css` 에 `--color-info` 추가 | **막힘 — 의도대로.** Edit 도 `sed -i` 도 차단됐다 |

3단계 차단은 설계대로다. `docs/maintenance.md` 가 "세션 안에서는 Bash 우회도 막는다" 고 주장하는데 실측으로 사실이었다.

### 발견 — 등록만 해도 전부 막혔다

2단계 직후 게이트가 `@theme 에 없는 원장 색: ['info']` 로 **모든 커밋을 막았다.** `확정층 ∪ 제안층 == @theme` 를 양방향 일치로 검사했기 때문이다. 등록(에이전트)과 배선(사람이 여는 `global.css`)은 주체가 다른데, 그 시차를 에러로 잡으니 **그 색과 무관한 작업까지 멈췄다.**

그리고 하필 그 메시지에 교정 지시문이 없었다. 다른 위반은 전부 무엇을 해야 하는지 붙는데 이 한 줄만 없었다 — 비개발자가 막히는 정확히 그 자리에서 스펙 §4.2 의 메시지 계약을 어기고 있었다.

### 고친 것

불변식을 한 방향으로 풀었다.

```
전: 확정층 ∪ 제안층 == @theme        (양방향)
후: @theme ⊆ 확정층 ∪ 제안층 + 확정층은 전부 배선   (한 방향)
```

- `@theme` 에 원장 밖 색이 있으면 여전히 차단 — 드리프트 방지는 그대로다
- 제안층 등록은 통과하고, 리포트가 "아직 `@theme` 에 없어 코드에서 쓸 수 없다" 로 알린다
- 확정층 누락 메시지에 교정 지시문을 붙였다

**완화가 만든 구멍도 같이 막았다.** 등록만 하고 `bg-info` 를 쓰면 Tailwind 가 그 유틸리티를 아예 만들지 않아 에러도 스타일도 없다 — `check_unwired_usage` 가 그 사용을 차단한다. 즉 **등록은 통과, 사용은 차단**이다.

## 컴포넌트 원장 검사 — 2026-09-03

`SHARED-COMPONENTS.md` 가 스스로 "게이트가 이 파일을 검사하지 않으므로 리터럴을 쓰면 안 잡힌다" 고 적어두고 있었다. 값을 토큰 참조(`{colors.accent}`)로 쓰는 형식으로 바꾼 이유가 기계 검사 가능하게 하려던 것이므로 `check_component_refs` 를 붙였다.

- 리터럴(`16px`·`#24F351`)을 잡는다 — `none`·`transparent` 만 예외다
- 원장에 없는 토큰(`{spacing.5}`)을 잡고 가까운 이름을 제안한다
- 없는 계열(`{elevation.high}`)을 잡는다

`spacing` 만 키 이름이 필요했다 — 원장이 순서 있는 배열이라서다. 코드가 쓰는 Tailwind 단계 표기(`1`=4px … `16`=64px)를 키로 삼았고, 이는 `CLAUDE.md` 와 `SPACING_INDEX` 가 이미 쓰는 표기라 새로 만든 규약이 아니다.

단위 테스트 20건을 더했다(128 → 148건).
