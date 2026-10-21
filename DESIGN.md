---
version: 1
name: 'PM pnpm'
description: 마브렉스 브랜드북 기반 디자인 시스템. origin brandbook 토큰은 마브렉스 공통이라 고정이고, 그 밖의 값은 프로젝트가 바꿀 수 있다. 이 문서(+@theme)가 토큰 단일 원장이다. 승격 대기 토큰은 DESIGN.proposed.yaml 에 있다.
inheritedFrom: marblex-web-shop
theme: light
colors:
  background:       { value: '#F8F8F8', origin: brandbook }
  background-shade: { value: '#DFDFDF', origin: brandbook }
  surface-dark:     { value: '#2A2A2A', origin: brandbook }
  surface-black:    { value: '#070707', origin: brandbook }
  text:             { value: '#070707', origin: brandbook }
  text-subtle:      { value: '#6A6A6A', origin: brandbook }
  text-disabled:    { value: '#AAAAAA', origin: brandbook }
  text-muted:       { value: '#C6C6C6', origin: brandbook }
  text-inverse:     { value: '#F8F8F8', origin: brandbook }
  accent:           { value: '#24F351', origin: brandbook }
  accent-pressed:   { value: '#1DC241', origin: brandbook }
  accent-deep:      { value: '#127A29', origin: brandbook }
  green-tint-01:    { value: '#66F785', origin: brandbook }
  green-tint-02:    { value: '#A7FAB9', origin: brandbook }
  green-tint-03:    { value: '#D3FDDC', origin: brandbook }
  green-shade-03:   { value: '#0B4918', origin: brandbook }
  grey-tint:        { value: '#EAEAEA', origin: brandbook }
  scrim:            { value: '#07070799', origin: derived, since: '2026-07-24' }
  warning:          { value: '#FF9F1C', origin: product, since: '2026-08-05' }
  danger:           { value: '#C41E1E', origin: product, since: '2026-08-05' }
  danger-tint:      { value: '#F9D7D7', origin: derived, since: '2026-08-05' }
rounded:
  origin: product
  small: '10px'
  card: '24px'
  pill: '999px'
borders:
  origin: product
  emphasis: '2px'
  hairline: '1px'
shadows:
  origin: product
  extruded: '4px 5px 0 #070707'
spacing:
  scale: ['4px', '6px', '8px', '12px', '16px', '24px', '32px', '48px', '64px']
  origin: product
  since: '2026-08-14'
typography:
  origin: product
  headline:    { fontFamily: 'GT Maru', fontWeight: 900, fontSize: { pc: '1.75rem', mobile: '1.375rem' }, letterSpacing: '-0.06em', lineHeight: '95%', textTransform: uppercase }
  subhead:     { fontFamily: 'GT Maru', fontWeight: 700, fontSize: { pc: '1.5rem', mobile: '1.25rem' }, letterSpacing: '-0.06em', lineHeight: '98%', textTransform: uppercase }
  body-head:   { fontFamily: 'GT Maru', fontWeight: 700, fontSize: '1.125rem', letterSpacing: '0', lineHeight: '101%', textTransform: uppercase }
  body-large:  { fontFamily: 'GT Maru', fontWeight: 400, fontSize: '1.125rem', letterSpacing: '0', lineHeight: '131%' }
  body:        { fontFamily: 'Inter', fontWeight: 400, fontSize: '1rem', letterSpacing: '0', lineHeight: '123%' }
  body-small:  { fontFamily: 'Inter', fontWeight: 400, fontSize: '0.875rem', letterSpacing: '0', lineHeight: '124%' }
  label:       { fontFamily: 'GT Maru', fontWeight: 700, fontSize: '0.875rem', letterSpacing: '0', lineHeight: '124%', textTransform: uppercase }
  label-small: { fontFamily: 'GT Maru', fontWeight: 500, fontSize: '0.75rem', letterSpacing: '0', lineHeight: '127%', textTransform: uppercase }
fontFamilies:
  origin: product
  latin-display: 'GT Maru'
  latin-text: 'Inter'
  hangul: 'Pretendard Variable'
  stack-maru: "'GT Maru', var(--font-inter-next), 'Pretendard Variable', sans-serif"
  stack-inter: "var(--font-inter-next), Inter, 'Pretendard Variable', sans-serif"
hangulTracking:
  origin: product
  scope: "html[lang='ko']"
  tokens: 'headline, subhead'
  letterSpacing: '-0.03em'
motion:
  origin: product
  duration-fast: '150ms'
  duration-standard: '250ms'
  ease-standard: 'ease-out'
  press-offset-x: '4px'
  press-offset-y: '5px'
  hover-lift: '-2px'
breakpoints:
  origin: product
  mobile-max: '768px'
---

# DESIGN.md — PM pnpm 디자인 시스템

## 1. 원장 선언

이 문서의 frontmatter와 `src/app/global.css` 의 `@theme` 가 토큰의 단일 원장이다. 둘이 어긋나면 게이트가 막는다.

**이 문서는 편집 금지다.** 새 토큰이 필요하면 `DESIGN.proposed.yaml` 에 근거와 함께 등록한다. 확정층으로 올리는 것은 디자이너·FE개발자의 승격 판단을 거친다.

## 2. 출처 — 무엇이 고정이고 무엇을 바꿀 수 있나

모든 값은 `marblex-web-shop`(pixeltamerzshop.marblex.io)에서 상속했다.

- **`origin: brandbook` — 마브렉스 공통. 고정이다.** 이 레포에서 바꾸지 않는다. 바뀌는 것은 브랜드북 자체가 바뀔 때뿐이다. 지금은 `colors` 의 brandbook 토큰만 해당한다.
- **`origin: product`·`derived` — 프로젝트가 바꿀 수 있다.** 템플릿에서 온 일반적인 기본값이다. 프로젝트에 맞지 않으면 바꾸고, 새로 필요한 값은 제안층(`DESIGN.proposed.yaml`)을 거쳐 들어온다.

`colors` 는 토큰마다, 나머지는 **블록마다** 출처를 단다. 한 블록 안에 브랜드북 값과 그 밖의 값이 섞이면 그 블록은 `product` 다 — 블록 전체가 브랜드북 값일 때만 `brandbook` 이다. 출처가 없는 블록은 게이트가 막는다.

`derived` 항목은 **도출식이 아니라 결과값이 박혀 있다.** `scrim` 은 `surface-black` 의 알파 60%, `danger-tint` 는 `danger` 에서 도출한 값이지만 둘 다 hex 리터럴이라 원본 토큰이 바뀌어도 따라가지 않는다. 원본을 바꾸면 이들도 함께 다시 계산해야 한다.

## 3. Colors

- 위 팔레트 밖의 색은 MUST NOT. hex 리터럴과 Tailwind 색 유틸리티 양쪽 모두 막는다.
- **순수 화이트·검정은 팔레트에 없다.** `#FFF`·`#FFFFFF` hex 와 `bg-white`·`text-black` 류 유틸리티 모두 MUST NOT. 밝은 면은 `background`, 어두운 면은 `surface-black` 을 쓴다.
- `origin` 은 값의 출처다. `brandbook`(마브렉스 브랜드북 실측 — 공통, 고정) · `product`(제품 정의 라운드에서 신설) · `derived`(기존 토큰에서 규칙으로 도출).

## 4. Shape · Spacing

- 모서리는 `rounded` 3단만 쓴다.
- 여백은 `spacing.scale` 9단만 쓴다. 임의 px 값 MUST NOT.
- `6px` 은 제목–부제 2행 패턴 전용 마이크로 스텝이다.

## 5. Typography

- 8토큰(`headline`·`subhead`·`body-head`·`body-large`·`body`·`body-small`·`label`·`label-small`)만 쓴다. `.typo-*` 클래스로 적용한다.
- 라틴 담당 서체는 `typography.*.fontFamily` 가 가리키고, 한글은 스택 끝의 `Pretendard Variable` 이 받는다. Pretendard를 스택 **끝**에 두는 이유는 앞의 두 서체가 한글 글리프를 갖지 않아 브라우저의 글자별 폴백이 한글만 넘기기 때문이다. 앞에 두면 라틴 렌더가 바뀐다.
- `headline`·`subhead` 만 모바일에서 축소한다(`breakpoints.mobile-max` 기준). CSS 변수 `--fs-headline`·`--fs-subhead` 로 구현한다.
- **한글 자간 예외** — `html[lang='ko']` 에서 `headline`·`subhead` 의 자간을 `-0.03em` 으로 푼다. `-0.06em` 은 GT Maru 라틴 기준 실측값이라 한글 음절 블록이 붙어 보인다. `letter-spacing` 은 스크립트별로 줄 수 없으므로 단위가 `lang` 이다. 행간에는 예외를 두지 않는다.
- 자간·행간을 임의로 조정하지 않는다. 예외를 늘리려면 이 절에 실측 근거를 남긴다.
- **CSS에서 외부 URL을 참조하지 않는다.** 서체는 자체 호스팅(woff2)하거나 빌드타임에 포함한다. CDN MUST NOT.

### 5.1 라이선스

- **GT Maru** — Grilli Type 상용. 라이선스는 X-shop 프로젝트 기준으로 확인됐다. **이 레포에서 쓸 수 있는지 확인됐는지 프로젝트 담당자에게 묻는다**(절차는 템플릿 원본의 `TEMPLATE.md`) — 범위 밖이면 서체를 바꾼다(`fontFamilies`·`typography`·`hangulTracking` 은 `product` 다. 자간은 GT Maru 기준 실측값이라 서체를 바꾸면 다시 잰다). woff2 4종을 `public/font/` 에 자체 호스팅한다.
- **Inter** — `next/font/google`. 빌드타임에 자체 호스팅으로 전환된다.
- **Pretendard** — npm `pretendard`, OFL-1.1. 저자 공식 릴리스의 variable dynamic subset을 **그대로** 쓴다. 직접 서브셋을 뜨면 OFL Modified Version 이 되어 Reserved Font Name(`Pretendard`)을 못 쓴다.

## 6. Motion

브랜드북에 직접적 실측 근거가 없는, 브랜드 원칙의 웹 번역이다.

- 기능 전환은 **150~250ms, ease-out** (`motion.duration-fast`/`duration-standard`/`ease-standard`). 장식성 장시간 애니메이션 MUST NOT.
- **시그니처 인터랙션 — 버튼 press 물성**: hover 시 `shadows.extruded` 그림자 등장 + `motion.hover-lift`(-2px) 부상, press 시 그림자 소멸 + `motion.press-offset-x`/`-y`(4px 5px)만큼 눌려 그림자 자리로 내려앉는다. 값은 `shadows.extruded` 의 오프셋과 같다 — 눌린 표면이 정확히 그림자 자리로 내려앉아야 하므로 두 값은 함께 움직인다.
- 모션 값은 **원장 변수를 직접 참조한다** — `translate-x-(--press-offset-x)`, `translate-y-(--hover-lift)`. Tailwind 여백 스케일로 같은 크기를 재현하는 것(`translate-y-1.25` = spacing×1.25 = 5px)은 MUST NOT: 그림자 오프셋이 `spacing.scale` 기본단위에 묶여 기본단위가 바뀌면 press 물성이 조용히 어긋나고, 9단 밖 배수(0.5·1.25)가 코드에 들어온다.
- 스프링(오버슈트 베지어)은 강조 등장 모먼트에만 SHOULD. 일반 전환에 MUST NOT.
- `prefers-reduced-motion` 존중 MUST — 사용자가 설정했으면 모션을 축소/제거한다. Tailwind 의 `motion-safe:`/`motion-reduce:` 변형을 쓴다.
- 지속시간은 `duration-(--duration-fast)` 처럼 원장 변수를 참조한다. `duration-200` 같은 Tailwind 기본 스케일 값은 원장 밖이다.

## 7. 의도적 보류

제품이 정해지지 않아 이번 라운드에서 결정하지 않는 항목이다. 여기 있는 항목은 **이미 논의해서 미룬 것**이므로, 필요해지면 제안층에 올리기 전에 이 표를 먼저 확인한다.

| 항목 | 사유 | 결정 시점 |
| --- | --- | --- |
| 기능색 `link` | 상속 원장에도 없다. 링크는 밑줄로 표현한다 | 제품 정의 라운드 |
| 컴포넌트 스펙 (Button·Card·Tag·Tab 등) | 이 레포에서 화면을 만들며 새로 만든다(`SHARED-COMPONENTS.md`). `marblex-web-shop` 스펙을 상속하지 않기로 했다 | 화면 설계 시 |
| z-index·toast·form·모달 | 제품 의존 | 제품 정의 라운드 |
| 레이아웃 브레이크포인트 | `breakpoints.mobile-max` 는 타이포 축소 기준일 뿐이다. 레이아웃 값은 화면이 생긴 뒤 정한다 | 화면 설계 시 |
| 일러스트·마스코트 | 미조사 | 필요 시 |
| 아이콘 세트 | 미조사 | 필요 시 |
