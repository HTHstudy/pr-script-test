---
# 컴포넌트 층 — DESIGN.md 의 컴포넌트 영역을 분리한 원장.
#
# 값은 리터럴로 쓰지 않는다. 전부 DESIGN.md 토큰 참조({...})다. 리터럴을 쓰면 그 순간
# 원장 밖 값이 되고, 이 파일은 게이트가 검사하지 않으므로 아무도 못 잡는다.
components:
  card:
    surface: '{colors.background-shade}'
    textColor: '{colors.text}'
    rounded: '{rounded.card}'
    shadow: none
    padding: '{spacing.4}'
    rowGap: '{spacing.2}'
    titleRowGap: '{spacing.1.5}'
    subtitleColor: '{colors.text-muted}'

  card-on-dark:
    surface: '{colors.surface-dark}'
    textColor: '{colors.text-inverse}'

  button-extruded:
    fill: '{colors.accent}'
    textColor: '{colors.text}'
    borderColor: '{colors.text}'
    borderWidth: '{borders.emphasis}'
    shadow: '{shadows.extruded}'
    rounded: '{rounded.pill}'
    typography: '{typography.label}'
    paddingBlock: '{spacing.3}'
    paddingInline: '{spacing.6}'
  button-extruded-light:
    fill: '{colors.background}'
  button-extruded-pressed:
    fill: '{colors.accent-pressed}'
    shadow: none
    translateX: '{motion.press-offset-x}'
    translateY: '{motion.press-offset-y}'

  button-outlined:
    fill: '{colors.accent}'
    textColor: '{colors.text}'
    borderColor: '{colors.text}'
    borderWidth: '{borders.emphasis}'
    shadow: none
    rounded: '{rounded.pill}'
    typography: '{typography.label}'
    paddingBlock: '{spacing.3}'
    paddingInline: '{spacing.6}'
  button-outlined-light:
    fill: '{colors.background}'
  button-outlined-on-dark:
    fill: transparent
    textColor: '{colors.text-inverse}'
    borderColor: '{colors.text-inverse}'

  button-solid:
    fill: '{colors.accent}'
    textColor: '{colors.text}'
    borderColor: none
    shadow: none
    rounded: '{rounded.pill}'
    typography: '{typography.label}'
    paddingBlock: '{spacing.3}'
    paddingInline: '{spacing.6}'
  button-solid-dark:
    fill: '{colors.surface-black}'
    textColor: '{colors.text-inverse}'
  button-solid-shade:
    fill: '{colors.background-shade}'
    textColor: '{colors.text}'

  button-disabled:
    fill: '{colors.background-shade}'
    textColor: '{colors.text-disabled}'
    borderColor: none
    shadow: none

  button-hovered:
    shadow: '{shadows.extruded}'
    translateY: '{motion.hover-lift}'
  button-pressed:
    fill: '{colors.accent-pressed}'
    shadow: none
    translateX: '{motion.press-offset-x}'
    translateY: '{motion.press-offset-y}'

  tag:
    fill: '{colors.accent}'
    textColor: '{colors.text}'
    rounded: '{rounded.pill}'
    typography: '{typography.label-small}'
    paddingBlock: '{spacing.1}'
    paddingInline: '{spacing.3}'
  tag-outlined:
    fill: transparent
    borderColor: '{colors.text}'
    borderWidth: '{borders.hairline}'
  tag-muted:
    fill: '{colors.grey-tint}'
    textColor: '{colors.text-subtle}'
---

# SHARED-COMPONENTS.md — 컴포넌트 원장

`DESIGN.md` 는 **토큰**을 정하고, 이 문서는 그 토큰으로 **무엇을 조립하는지**를 정한다. 둘이 합쳐 원장이다.

`DESIGN.md` §7 이 컴포넌트 스펙을 "화면 설계 시" 로 미뤄뒀고, 지금이 그 시점이다.

## 1. 명세와 구현은 다르다

| | 무엇 | 언제 |
| --- | --- | --- |
| 이 문서 | **명세** — 만든다면 이런 모양이다 | 미리 정한다 |
| `src/shared/ui/` | **구현** — 실제 파일 | 두 번째 사용처가 생기면 |

명세가 있다고 구현이 있는 것은 아니다. 화면 안에서 만들어 쓰다가 두 번째 사용처가 생기면 그때 올린다. **명세는 앞서 가도 되지만 구현은 아니다** — 안 쓰는 컴포넌트를 미리 만들면 유지비만 든다.

현재 구현: 없음.

## 2. 값은 토큰 참조로 쓴다

frontmatter 의 값은 전부 `{...}` 참조다. 리터럴(`16px`·`#24F351`·`p-4`)을 쓰지 않는다 — 이 파일은 토큰 게이트가 검사하지 않으므로, 리터럴을 쓰면 원장 밖 값이 들어와도 아무도 못 잡는다.

| 참조 | 가리키는 곳 |
| --- | --- |
| `{colors.<이름>}` | `DESIGN.md` frontmatter `colors` |
| `{rounded.<이름>}` | `rounded` — `small`·`card`·`pill` |
| `{borders.<이름>}` | `borders` — `emphasis`(2px)·`hairline`(1px) |
| `{shadows.<이름>}` | `shadows` — `extruded` |
| `{typography.<이름>}` | `typography` 8토큰 |
| `{motion.<이름>}` | `motion` |
| `{spacing.<단계>}` | `spacing.scale` 9단 |

`spacing` 만 단계 이름이 필요하다 — 원장이 순서 있는 배열로 갖고 있기 때문이다. 코드에서 쓰는 Tailwind 표기를 키로 삼는다.

```
1=4px  1.5=6px  2=8px  3=12px  4=16px  6=24px  8=32px  12=48px  16=64px
```

**원장에 없는 값이 필요하면 여기에 리터럴로 적지 말고 `DESIGN.proposed.yaml` 로 간다.**

## 3. Card

콘텐츠 한 덩어리를 담는 표면.

- **MUST NOT — 기본 그림자를 달지 않는다.** `shadows.extruded` 는 눌리는 것의 물성이지 표면 장식이 아니다. 누를 수 없는 배너·안내 박스에 정적으로 다는 것도 같은 위반이다.
- **MUST — 제목 2행 패턴은 `{spacing.1.5}`(6px).** 1행 강조 텍스트 + 2행 `text-subtle`/`text-muted` 뮤트. `DESIGN.md` §4 가 6px 을 이 패턴 전용 마이크로 스텝으로 지정한다.
- 다크 섹션 위에서는 `card-on-dark` 를 쓴다.

근거: 피그마 원장 `Marblex Guidelines [FINAL]` 디지털 예시(`348:16428`) — `rounded.card`, 기본 그림자 없음, 2행 6px.

## 4. Button

3티어 위계다. 티어는 **강조도**로 고르며 색으로 고르지 않는다.

| 티어 | 구성 | 용도 |
| --- | --- | --- |
| `button-extruded` | 채움 + `borders.emphasis` 아웃라인 + `shadows.extruded` | 최강조 |
| `button-outlined` | 채움 + `borders.emphasis` 아웃라인 | 표준 CTA |
| `button-solid` | 플랫 채움, 아웃라인 없음 | 일반·저강조 |

- **SHOULD — `button-extruded` 는 화면당 하나.** 최강조가 둘이면 강조가 아니다.
- **MUST NOT — `surface-black` 배경 위에 `button-extruded` 를 쓰지 않는다.** 그림자가 배경에 묻힌다(브랜드북 "Not on Black").
- **MUST — 다크 배경 위 outlined 는 `button-outlined-on-dark`** (투명 채움 + `text-inverse` 스트로크).
- **MUST NOT — 비활성을 직접 칠하지 않는다.** `button-disabled` 를 쓴다. 아웃라인·그림자 없음.

### 눌림 물성

`DESIGN.md` §6 시그니처 인터랙션이다. **티어마다 정지 상태가 다르므로 hover 동작도 다르다.**

| 티어 | 정지 | hover | press |
| --- | --- | --- | --- |
| `extruded` | 그림자 **있음** | `hover-lift` 부상 | 그림자 소멸 + `press-offset` 만큼 내려앉음 |
| `outlined` · `solid` | 그림자 없음 | 그림자 **등장** + `hover-lift` 부상 | 그림자 소멸 + `press-offset` 만큼 내려앉음 |

- **MUST — accent 채움의 눌림색은 `{colors.accent-pressed}`.** 원장이 이 색의 용도를 "눌림" 으로 지정한다. 밝기를 임의로 조절하지 않는다.

- **MUST — 크기는 원장 변수를 직접 참조한다.** `translate-y-(--hover-lift)`, `translate-x-(--press-offset-x)`. Tailwind 여백 스케일로 같은 크기를 재현하는 것(`translate-y-1.25`)은 `DESIGN.md` §6 이 MUST NOT 으로 막는다.
- **MUST — `prefers-reduced-motion` 존중.** `motion-safe:`/`motion-reduce:` 로 감싼다.
- `press-offset` 값은 `shadows.extruded` 의 오프셋과 같다. 눌린 표면이 정확히 그림자 자리로 내려앉기 위한 것이므로 두 값은 함께 움직인다.

근거: 3티어 구조 — 피그마 원장 버튼 배경 매트릭스(`348:3072`). 눌림 물성 — `DESIGN.md` §6.

## 5. Tag

분류·상태 라벨. 누르지 않는다.

- **MUST NOT — Tag 를 버튼으로 만들지 않는다.** 누를 수 있어야 하면 `button-solid` 를 쓴다.
- 높이를 직접 지정하지 않는다. `typography.label-small` + `paddingBlock` 의 결과로 정해진다.

근거: 피그마 원장 디지털 예시 — `rounded.pill`, `typography.label-small`, solid 또는 1px 아웃라인.

## 6. 가져오지 않은 것

픽셀테이머즈(`marblex-web-shop`) 원장에 있으나 이 문서가 **의도적으로 뺀 것**이다. `DESIGN.md` §7 이 "`marblex-web-shop` 스펙을 상속하지 않기로 했다" 고 선언했으므로, 가져온 것에는 위처럼 피그마 근거를 붙였고 아래는 그 근거가 없거나 이 레포에 맞지 않는다.

| 항목 | 왜 안 가져왔나 |
| --- | --- |
| Button 사이즈 `sm 36 / md 44 / lg 56` | 웹상점이 "신규 제정" 이라고 표시한 자체 추가분이다. 그리고 **원장 여백 9단으로 44px 를 만들 수 없다** — 넣으면 리터럴이 된다 |
| 버튼 배경 매트릭스 26행 | 색 조합이라, 팔레트를 잠정값으로 보던 시점에 가져오지 않았다. 브랜드북 색은 마브렉스 공통·고정으로 정리됐으므로 다시 볼 수 있다. 지금은 3티어 **구조**만 가져왔다 |
| Tab 언더라인 패턴 | 웹상점이 "브랜드북·Figma 미수록" 이라고 표시했다. 자매 프로덕트 정합용 |
| NavPill | 목록 필터·페이지네이션용. 이 레포에 그 화면이 아직 없다 |
| 링크 `underline-offset-3` | 웹상점 자기 화면 3종에서 도출한 값이다 |
| ExpressiveText | 마케팅 전용이며 기능 UI 에 MUST NOT 인 것이다 |

## 7. 이 문서가 정한 값 — 디자이너 확인 필요

피그마 원장이 정하지 않아 **이 문서가 결정한** 값이다. 디자이너 확인 라운드에서 먼저 볼 목록이다.

| 값 | 정한 것 | 근거 |
| --- | --- | --- |
| 버튼 모서리 | `{rounded.pill}` | 원장 `rounded` 3단 중 선택. 피그마 매트릭스는 반경을 지정하지 않는다 |
| 버튼 여백 | `{spacing.3}` / `{spacing.6}` | 9단 안에서 고름. 결과 높이는 약 41px |
| Card 표면색 | `{colors.background-shade}` | 실측 근거 표의 용도가 "구분 배경" 이다 |
| Card 안쪽 여백 | `{spacing.4}` | 어느 원장에도 규정이 없었다. 여기서 정한다 |
| Tag 여백 | `{spacing.1}` / `{spacing.3}` | 피그마의 26px 높이를 9단으로 재현할 수 없어 여백으로 정했다 |

## 8. Do's and Don'ts

| Do | Don't |
| --- | --- |
| 이 문서의 레시피대로 조립 | 화면마다 클래스 묶음을 새로 지어냄 |
| 표면은 `div`, 그 안의 요소가 눌림 | 표면 자체를 `<button>` 으로 |
| `shadows.extruded` 는 눌리는 것에만 | 배너·안내 박스에 정적 그림자 |
| 강조도로 티어 선택 | 색이 예뻐서 티어 선택 |
| 최강조 버튼 화면당 하나 | extruded 를 여러 개 |
| `button-disabled` 레시피 | 비활성을 직접 회색으로 칠함 |
| 상태 표시는 Tag | 누를 수 없는 Tag 에 클릭 핸들러 |
| 모션 크기는 `(--변수)` 직접 참조 | `translate-y-1.25` 처럼 여백 스케일로 재현 |
| 원장에 없으면 `DESIGN.proposed.yaml` | 이 파일에 리터럴로 적기 |

## 9. 컴포넌트를 추가할 때

frontmatter 에 레시피를, 본문에 절을 넣는다.

```yaml
  <이름>:
    <속성>: '{<계열>.<토큰>}'
```

```markdown
## <이름>

한 줄 정의 — 특히 **하지 않는 것**.

- **MUST / MUST NOT** — 규칙과 이유

근거: <피그마 노드 · DESIGN.md § · 또는 "이 문서 결정">
```

`근거` 줄이 없으면 넣지 않는다. 출처를 못 대는 규칙은 누군가의 취향이고, 취향은 원장에 들어가지 않는다.
