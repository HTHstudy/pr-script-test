"""원장 ↔ CSS ↔ 코드 대조 규칙."""
import difflib
import re

WHITE_BLACK_UTIL = re.compile(
    r'\b(?:bg|text|border|outline|ring|divide|fill|stroke|decoration|shadow'
    r'|from|via|to|accent|caret|placeholder)'
    r'(?:-(?:t|r|b|l|s|e|x|y|top|right|bottom|left|inline|block|offset))?'
    r'-(?:white|black)\b')


def check_theme(confirmed, proposed, shape, css, rejected=None):
    """@theme ⊆ 확정층 ∪ 제안층(활성) 이고 확정층은 전부 배선됐는지 검사한다.

    한 방향이다. @theme 에 원장 밖 색이 있으면 막지만(드리프트 방지), 제안층에 등록만
    되고 아직 @theme 에 없는 것은 막지 않는다 — 등록과 배선의 주체가 다르기 때문이다.
    그 시차가 만드는 구멍(등록만 하고 bg-info 를 쓰면 조용히 무효)은 check_unwired_usage
    가 막는다.

    proposed 는 이미 반려분을 뺀 활성 제안만 담아 호출한다(호출부 책임).
    rejected: {name: meta} — 반려된 제안 토큰. @theme 에 그 이름이 여전히 남아 있으면
    "원장에 없는 색"이 아니라 반려 사실을 명시한 메시지를 낸다.
    """
    errors = []
    rejected = rejected or {}
    want = {k: v['value'] for k, v in confirmed.items()}
    want.update({k: v['value'] for k, v in proposed.items()})

    # 값 형태와 무관하게 키 집합부터 잡는다 — 원래는 hex 값만 캡처해서 oklch()/rgb() 같은
    # 비-hex 값을 쓴 --color-* 가 got 에 아예 안 들어가 extra/drift 어느 쪽에도 안 잡혔다
    # (F1). '*' 는 [\w-] 밖이라 --color-*: initial; 리셋 라인은 여전히 캡처되지 않는다.
    HEX_RE = re.compile(r'#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?')
    color_decls = re.findall(r'--color-([\w-]+):\s*([^;]+);', css)
    got = {}
    non_hex_colors = []
    for k, v in color_decls:
        v = v.strip()
        if HEX_RE.fullmatch(v):
            got[k] = v.upper()
        else:
            got[k] = v
            non_hex_colors.append((k, v))
    non_hex_keys = {k for k, _ in non_hex_colors}

    # 확정층 누락만 에러다. 제안층은 등록(에이전트)과 배선(사람이 여는 global.css)의
    # 주체가 달라 시차가 정상이며, 그 시차를 에러로 잡으면 등록하는 순간 그 색과 무관한
    # 작업까지 커밋이 막힌다. 제안층 미배선은 unwired_proposed() 가 통지로 처리하고,
    # 코드가 실제로 그 색을 쓰면 scan_code 가 막는다.
    missing = sorted(set(confirmed) - set(got))
    extra = sorted(set(got) - set(want))
    drift = sorted(k for k in (set(want) & set(got)) - non_hex_keys if want[k] != got[k])
    if missing:
        errors.append(
            f"@theme 에 없는 확정층 색: {missing} — src/app/global.css 의 @theme 에 "
            f"--color-<이름> 으로 추가해야 코드에서 쓸 수 있다. 그 파일은 잠겨 있으므로 "
            f"직접 고치지 말고 사용자에게 요청하라.")
    rejected_extra = sorted(k for k in extra if k in rejected)
    plain_extra = sorted(k for k in extra if k not in rejected)
    for k in rejected_extra:
        errors.append(
            f"반려된 제안 토큰 {k}({got[k]}) 를 아직 사용 중이다 — "
            f"확정층 값으로 교체하고 @theme 에서 제거하라")
    if plain_extra:
        errors.append(f"원장에 없는 @theme 색: {plain_extra}")
    for k in drift:
        errors.append(f"@theme 색 값 드리프트: {k} 원장={want[k]} CSS={got[k]}")
    for k, v in sorted(non_hex_colors):
        errors.append(
            f"@theme --color-{k} 값이 hex 형식이 아니다: {v} — #RRGGBB 또는 #RRGGBBAA 만 허용한다")

    # 이 두 리셋 라인이 없으면 Tailwind 기본 팔레트·radius 유틸리티가 그대로 살아난다 —
    # 지우는 게 이 게이트를 우회하는 가장 값싼 방법이다(F2). 존재 자체를 강제한다.
    if not re.search(r'--color-\*:\s*initial;', css):
        errors.append(
            "@theme 에 '--color-*: initial;' 리셋이 없다 — "
            "Tailwind 기본 팔레트(bg-blue-500 등)가 되살아난다")
    if not re.search(r'--radius-\*:\s*initial;', css):
        errors.append(
            "@theme 에 '--radius-*: initial;' 리셋이 없다 — "
            "Tailwind 기본 radius 유틸리티(rounded-full 등)가 되살아난다")

    for key, want_v in sorted(shape['rounded'].items()):
        var = f'--radius-{key}'
        m = re.search(rf'{var}:\s*([^;]+);', css)
        got_v = m.group(1).strip() if m else None
        if want_v != got_v:
            errors.append(f"{var} 불일치: 원장={want_v} CSS={got_v or '없음'}")

    css_radius_keys = set(re.findall(r'--radius-([\w-]+):', css))
    extra_radius = sorted(f'--radius-{k}' for k in css_radius_keys - set(shape['rounded']))
    if extra_radius:
        errors.append(f"원장에 없는 --radius-*: {extra_radius}")

    if shape['shadow_extruded'] and f"--shadow-extruded: {shape['shadow_extruded']}" not in css:
        errors.append(f"--shadow-extruded 불일치(원장: {shape['shadow_extruded']})")

    ledger_shadow_keys = {'extruded'} if shape['shadow_extruded'] else set()
    css_shadow_keys = set(re.findall(r'--shadow-([\w-]+):', css))
    extra_shadow = sorted(f'--shadow-{k}' for k in css_shadow_keys - ledger_shadow_keys)
    if extra_shadow:
        errors.append(f"원장에 없는 --shadow-*: {extra_shadow}")

    return errors


REMEDIATION = (
    '팔레트에서 가장 가까운 토큰으로 교체하라. 정말 새 색이 필요하면 직접 추가하지 말고 '
    '사용자에게 물어라. DESIGN.md는 편집 금지다.'
)

# F5 — 위 REMEDIATION 은 색 전용 문구다. 예전엔 이 하나를 여백·모션·인라인 스타일·임의값
# 위반에도 그대로 붙였다 — p-5 를 쓴 에이전트가 "새 색이 필요하냐"는 안내를 받는 식으로,
# 메시지가 엉뚱한 수리를 유도했다(실제로 이 레포에서 두 번 일어난 사고). 위반 종류별로
# 갈라 맞는 교정문구만 붙인다. scan_code(색 전용)는 위 REMEDIATION 을 계속 쓴다.
REMEDIATION_SPACING = (
    '원장 여백 9단(0/1/1.5/2/3/4/6/8/12/16/auto/px) 중 가장 가까운 값으로 교체하라. 정말 새 '
    '여백이 필요하면 직접 추가하지 말고 사용자에게 물어라. DESIGN.md는 편집 금지다.'
)
REMEDIATION_MOTION = (
    '원장 motion 토큰(예: duration-(--duration-fast), ease-standard)으로 교체하라. 정말 새 '
    '모션 값이 필요하면 직접 추가하지 말고 사용자에게 물어라. DESIGN.md는 편집 금지다.'
)
REMEDIATION_INLINE_STYLE = (
    'className 유틸리티로 옮겨라. 인라인 style은 게이트가 값을 추적할 수 없는 자리다. 정말 '
    '인라인이 꼭 필요하면 직접 추가하지 말고 사용자에게 물어라.'
)
REMEDIATION_ARBITRARY = (
    '임의값 대신 원장에 있는 토큰 유틸리티로 교체하라. 정말 새 값이 필요하면 직접 추가하지 '
    '말고 사용자에게 물어라. DESIGN.md는 편집 금지다.'
)


def _lineno(text, pos):
    """0-based 문자 위치 → 1-based 줄 번호."""
    return text.count('\n', 0, pos) + 1


def scan_code(allowed_values, files, rejected=None):
    """앱 코드에서 팔레트 밖 색 사용을 찾는다.

    allowed_values: 대문자 hex 문자열 집합 (확정층 ∪ 제안층 활성분 — 호출부가 반려분을 뺀다)
    files: (상대경로, 내용) 튜플의 시퀀스
    rejected: {name: meta} — 반려된 제안 토큰. 코드가 그 값을 여전히 쓰고 있으면
    "원장에 없는 색"이 아니라 반려 사실을 명시한 메시지를 낸다.

    off-ledger 메시지(과 화이트/검정 계열 메시지)는 스펙 §4.2 의 계약을 따른다 —
    파일:줄번호 + 에이전트가 무엇을 해야 하는지(교정 지시문)까지 담는다. 훅이 붙으면
    이 stderr 텍스트를 에이전트가 그대로 읽고 행동하므로, 모호함은 여기서 잘못된
    행동으로 이어진다(F3). 반려 토큰 메시지는 이미 이 기준을 만족해 손대지 않는다.
    """
    errors = []
    rejected = rejected or {}
    rejected_by_value = {m['value']: n for n, m in rejected.items() if m.get('value')}
    for rel, text in files:
        for m in re.finditer(r'#[0-9A-Fa-f]{3,8}\b', text):
            h = m.group(0)
            hu = h.upper()
            if len(h) in (7, 9) and hu in allowed_values:
                continue
            if len(h) in (7, 9) and hu in rejected_by_value:
                errors.append(
                    f"{rel}: 반려된 제안 토큰 {rejected_by_value[hu]}({hu}) 를 아직 사용 중이다 — "
                    f"확정층 값으로 교체하고 코드에서 제거하라")
                continue
            lineno = _lineno(text, m.start())
            errors.append(
                f"DESIGN.md에 없는 색 {h}을 {rel}:{lineno}에 썼다. {REMEDIATION}")

        white_m = re.search(r'#(?:fff|FFF)\b', text)
        white_pos = white_m.start() if white_m else text.upper().find('#FFFFFF')
        if white_pos != -1:
            lineno = _lineno(text, white_pos)
            errors.append(
                f"{rel}:{lineno}: 순수 화이트 hex 사용 — 팔레트에 없다. {REMEDIATION}")

        for u in sorted(set(WHITE_BLACK_UTIL.findall(text))):
            pos = text.find(u)
            lineno = _lineno(text, pos) if pos != -1 else '?'
            errors.append(
                f"{rel}:{lineno}: 팔레트 밖 색 유틸리티 {u} — 순수 화이트·검정은 팔레트에 없다. "
                f"{REMEDIATION}")
    return errors


# 원장 typography.fontFamily 값 → @theme CSS 변수 이름 번역표. 문자열 변환으로 유도할 수
# 없어(맞춤 이름 규칙이 없다 — 'GT Maru' → '--font-maru' 는 표기 관례일 뿐 규칙이 아니다)
# 표로 유지한다. 원장에 세 번째 서체가 추가되면 반드시 이 표에도 항목을 추가하라 — 추가하지
# 않으면 아래 검사가 그 fontFamily 를 "매핑되지 않음"으로 보고해 막는다(F5. 이전엔 매핑에
# 없는 이름이 있으면 want_var 가 None 이 되어 검사 자체가 조용히 사라졌다 — fail-open 이었다).
FONT_VAR = {'GT Maru': '--font-maru', 'Inter': '--font-inter'}

MOTION_VAR_RE = re.compile(r'--((?:duration|ease|press|hover)-[\w-]+):\s*[^;]+;')


def _class_body(css, name):
    m = re.search(rf'\.typo-{re.escape(name)}\s*\{{([^}}]+)\}}', css)
    return m.group(1) if m else None


def check_typography(typography, hangul, css):
    """원장 typography ↔ .typo-* 클래스를 대조한다. 양방향이다 — 원장에 있는데 CSS에
    없는 것과, CSS에 있는데 원장에 없는 .typo-* 클래스 둘 다 잡는다."""
    errors = []
    for name, tok in sorted(typography.items()):
        body = _class_body(css, name)
        if body is None:
            errors.append(f"typo-{name}: CSS 에 .typo-{name} 클래스가 없다")
            continue
        if tok['fontWeight'] and f"font-weight: {tok['fontWeight']};" not in body:
            errors.append(f"typo-{name}: weight 불일치 (원장 {tok['fontWeight']})")
        if tok['lineHeight'] and f"line-height: {tok['lineHeight']}" not in body:
            errors.append(f"typo-{name}: line-height 불일치 (원장 {tok['lineHeight']})")
        if tok['letterSpacing'] == '0':
            # '0'은 "letter-spacing 선언이 없다"와 같은 뜻이다 — 실제 8토큰 중 6개가 이
            # 형태이고 CSS 도 그 6개에 letter-spacing 을 아예 안 쓴다. 선언 자체가 없으면
            # 통과, 0이 아닌 값이 있으면 잡는다.
            ls_m = re.search(r'letter-spacing:\s*([^;]+);', body)
            if ls_m and ls_m.group(1).strip() != '0':
                errors.append(
                    f"typo-{name}: letter-spacing 불일치 (원장 0, CSS {ls_m.group(1).strip()})")
        elif tok['letterSpacing'] and f"letter-spacing: {tok['letterSpacing']};" not in body:
            errors.append(f"typo-{name}: letter-spacing 불일치 (원장 {tok['letterSpacing']})")
        if tok['fontSize'] and f"font-size: {tok['fontSize']}" not in body:
            errors.append(f"typo-{name}: font-size 불일치 (원장 {tok['fontSize']})")
        if tok['fontSizeResponsive']:
            pc, mobile = tok['fontSizeResponsive']
            var = f'--fs-{name}'
            decls = re.findall(rf'{var}:\s*([\d.]+rem)', css)
            if decls != [pc, mobile]:
                errors.append(
                    f"typo-{name}: 반응형 font-size 불일치 (원장 pc {pc}/mobile {mobile}, CSS {decls})")
            if f'font-size: var({var})' not in body:
                errors.append(f"typo-{name}: font-size var({var}) 미사용")
        has_uppercase = 'text-transform: uppercase' in body
        if tok['uppercase'] and not has_uppercase:
            errors.append(f"typo-{name}: uppercase 누락")
        elif not tok['uppercase'] and has_uppercase:
            errors.append(f"typo-{name}: uppercase 과다 (원장에 textTransform 없음)")
        face = tok['fontFamily']
        if face not in FONT_VAR:
            errors.append(
                f"typo-{name}: 매핑되지 않은 fontFamily '{face}' — FONT_VAR 표에 추가하라 "
                f"(scripts/design_tokens/checks.py)")
        else:
            want_var = FONT_VAR[face]
            if f'font-family: var({want_var})' not in body:
                errors.append(f"typo-{name}: font-family 불일치 (원장 {face} → var({want_var}))")

    # 역방향 — CSS 에 .typo-* 클래스가 있는데 DESIGN.md typography 에 없는 경우.
    css_typo_names = set(re.findall(r'\.typo-([\w-]+)', css))
    extra_typo = sorted(css_typo_names - set(typography))
    if extra_typo:
        errors.append(
            f"DESIGN.md typography 에 없는 .typo-*: {[f'typo-{n}' for n in extra_typo]}")

    if not hangul['scope'] or not hangul['letterSpacing']:
        errors.append('DESIGN.md hangulTracking.scope/letterSpacing 누락')
    else:
        for tok_name in hangul['tokens']:
            if tok_name not in typography:
                continue
            if f"{hangul['scope']} .typo-{tok_name}" not in css:
                errors.append(f"한글 자간 예외 선택자 누락: {hangul['scope']} .typo-{tok_name}")
        m = re.search(re.escape(hangul['scope']) + r"[^{]*\{\s*letter-spacing:\s*([^;]+);", css)
        got = m.group(1).strip() if m else None
        if got != hangul['letterSpacing']:
            errors.append(f"한글 자간 값 불일치: 원장={hangul['letterSpacing']} CSS={got or '없음'}")
    return errors


def check_font_stacks(stacks, css):
    """원장 fontFamilies.stack-* ↔ @theme --font-* 를 대조한다.

    타이포 검사는 .typo-* 가 올바른 var 를 쓰는지만 본다. 그 var 가 무엇으로 풀리는지는
    보지 않아 한글 폴백이 빠져도 통과한다 — 여기서 막는다.
    """
    errors = []
    if len(stacks) != 2:
        errors.append('DESIGN.md fontFamilies.stack-maru/stack-inter 누락')
    for name, want in sorted(stacks.items()):
        m = re.search(rf'--font-{name}:\s*([^;]+);', css)
        got = m.group(1).strip() if m else '없음'
        if got != want:
            errors.append(f"--font-{name} 스택 불일치\n    CSS={got}\n    원장={want}")
    return errors


EXTERNAL_URL_RE = re.compile(
    # 스킴(https?:)은 있어도 되고 없어도 된다 — //host 형태(프로토콜 상대 URL)도 브라우저가
    # 그대로 외부에서 받아온다. 호스트에 점(.)이 최소 하나 있을 것을 요구해 진짜 호스트명과
    # 구분한다: 'pretendard/dist/...' 같은 슬래시 없는 bare specifier, url('/font/...') 같은
    # 슬래시 1개짜리 루트 상대 로컬 경로는 애초에 '//' 를 포함하지 않아 여기 안 걸린다.
    r'(?:https?:)?//(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}[^\s\'")]*')


def check_no_external_url(css):
    """CSS 의 외부 URL 참조를 막는다. ESLint 는 CSS 를 보지 않는다."""
    return [f'global.css 외부 URL 금지: {m.group(0)}'
            for m in EXTERNAL_URL_RE.finditer(css)]


def check_motion(motion, css):
    """원장 motion ↔ @theme CSS 변수를 대조한다. 양방향이다.

    변수 이름은 `--{key}` 로 파생한다. 번역표를 두면 원장과 CSS 가 서로 다른 이름을
    쓰면서도 게이트가 조용히 봉합해 준다 — rounded.full/--radius-pill 이 그렇게 어긋났다.

    상속 원장(marblex-web-shop)은 motion 을 CSS 로 내보내지 않아 코드가 Tailwind 기본
    duration-200 으로 드리프트했다. 여기서 1:1 로 묶는다.

    역방향도 본다 — CSS 에 --duration-*/--ease-*/--press-*/--hover-* 변수가 있는데 원장
    motion 에 없는 경우. --color-*/--radius-* 리셋 라인과 --fs-* 반응형 변수(타이포
    파생)는 이 네 접두사에 안 걸리므로 오탐하지 않는다.
    """
    if not motion:
        return ['DESIGN.md motion 블록 누락']
    errors = []
    for name, want in sorted(motion.items()):
        var = f'--{name}'
        m = re.search(rf'{var}:\s*([^;]+);', css)
        got = m.group(1).strip() if m else None
        if got != want:
            errors.append(f'{var} 불일치: 원장={want} CSS={got or "없음"}')

    css_motion_vars = set(MOTION_VAR_RE.findall(css))
    extra_motion = sorted(css_motion_vars - set(motion))
    if extra_motion:
        errors.append(
            f"DESIGN.md motion 에 없는 CSS 변수: {[f'--{n}' for n in extra_motion]}")
    return errors


# DESIGN.md spacing 9단(4/6/8/12/16/24/32/48/64px)에 대응하는 Tailwind 인덱스.
# Tailwind 기본 스페이싱은 0.25rem 배수이므로 9단이 정확히 이 집합으로 사상된다.
SPACING_INDEX = {'0', '1', '1.5', '2', '3', '4', '6', '8', '12', '16', 'auto', 'px'}

# 여백 계열 접두사만 본다. w-/h-/inset- 등은 레이아웃 치수이지 원장이 말하는 여백이 아니다.
SPACING_PREFIX = (
    'p', 'px', 'py', 'pt', 'pr', 'pb', 'pl', 'ps', 'pe',
    'm', 'mx', 'my', 'mt', 'mr', 'mb', 'ml', 'ms', 'me',
    'gap', 'gap-x', 'gap-y', 'space-x', 'space-y',
)
SPACING_RE = re.compile(
    r'-?\b(' + '|'.join(sorted(SPACING_PREFIX, key=len, reverse=True)) + r')-([\w.]+)\b')

# Tailwind 임의값 문법. 대괄호는 원장 밖 값을 직접 박는 통로다.
# 괄호 문법(duration-(--duration-fast))은 원장 변수를 참조하는 것이므로 허용한다.
ARBITRARY_RE = re.compile(r'\b([\w-]+)-\[([^\]\s]+)\]')

# F1 — 임의 *속성* 문법: `[padding:13px]`, `[color:rgb(59,130,246)]`. ARBITRARY_RE 는
# `prefix-[...]` 형태만 보므로 접두사 없는 이 형태는 그냥 통과한다. 대괄호 앞이 단어문자·
# `]`·`)` 가 아니어야 한다는 조건으로 arr[0], obj["key"], Array<[string, number]> 같은
# 배열/인덱스/제네릭 문법과 구분한다(색 리터럴이 없는 코드베이스 전수 확인, 오탐 0건).
ARBITRARY_PROP_RE = re.compile(r'(?<![\w\]\)])\[[a-zA-Z-]+:[^\]\s]+\]')

# F4 — data-[state=open]:, aria-[current=page]:, supports-[display:grid]:, max-[600px]:,
# group-data-[open]: 같은 표준 Tailwind 변형 선택자. 값이 아니라 선택자 문법이므로 임의값
# 검사에서 뺀다. 대괄호 바로 앞이 이 접두사들이고 바로 뒤가 `:` 일 때만 예외로 본다 —
# group-data-[open]: 은 `data-` 로도 걸린다(접두사가 겹쳐도 무방, 하나만 맞으면 된다).
_VARIANT_PREFIXES = ('data-', 'aria-', 'supports-', 'has-', 'group-', 'peer-', 'min-', 'max-')
VARIANT_BRACKET_RE = re.compile(
    '(?:' + '|'.join(f'(?<={p})' for p in _VARIANT_PREFIXES) + r')\[[^\]]+\](?=:)'
)

INLINE_STYLE_RE = re.compile(r'\bstyle\s*=\s*\{\{')

DURATION_RE = re.compile(r'\bduration-(\d+)\b')
# F6 — `ease-(--ease-spring)` 은 원장 CSS 변수 참조다. 앞의 `(?<!-)` 가 없으면 이 문자열 안의
# `--ease-spring` 에서 두 번째 하이픈 뒤 "ease-spring" 부분을 별개의 유틸리티로 오인해 잡는다
# (허용 이징이 우연히 'standard' 하나뿐이라 지금까지 드러나지 않았을 뿐이다).
EASE_RE = re.compile(r'(?<!-)\bease-([a-z-]+)\b')

TSX_SUFFIXES = ('.tsx', '.jsx')

# 이 네 검사(임의값·여백·duration·ease)는 전부 Tailwind 클래스명 문법을 읽는다 —
# 클래스명은 코드에만 산다, CSS 에는 안 산다. .css 는 정의부다: --ease-standard: ease-out;
# 의 ease-out 은 합법적인 CSS timing-function 키워드고, --duration-fast: 150ms 의 150ms 는
# 합법적인 duration 값이다 — 우연히 유틸리티 클래스명과 같은 형태일 뿐이다. .css 내용은
# 이미 check_theme/check_typography/check_motion/check_no_external_url 과 scan_code 의
# hex 스캔이 대조한다. 이 프로젝트는 @apply 를 쓰지 않으므로 .css 안에 Tailwind 유틸리티
# 클래스명이 나타날 일이 없다 — 스킵해도 잃는 게 없다.
CODE_SUFFIXES = ('.ts', '.tsx', '.js', '.jsx')


def scan_utilities(files, allowed_ease=('standard',)):
    """원장 밖 값이 유틸리티·인라인 스타일로 들어오는 것을 막는다.

    hex 리터럴 검사(scan_code)만으로는 bg-[#3B82F6] 도, p-[13px] 도, [padding:13px] 같은
    임의 *속성* 문법(F1)도, style={{}} 도 잡히지 않는다. DESIGN.md 가 MUST 로 선언한 여백
    9단과 모션 토큰이 강제되는 자리도 여기다.

    data-[state=open]: 같은 표준 변형 선택자는 임의값이 아니므로 뺀다(F4).
    """
    errors = []
    for rel, text in files:
        if not rel.endswith(CODE_SUFFIXES):
            continue

        def at(pos, msg, remediation):
            errors.append(f'{rel}:{_lineno(text, pos)}: {msg} {remediation}')

        variant_starts = {vm.start() for vm in VARIANT_BRACKET_RE.finditer(text)}

        for m in ARBITRARY_RE.finditer(text):
            bracket_start = m.start(2) - 1
            if bracket_start in variant_starts:
                continue
            at(m.start(), f'Tailwind 임의값 {m.group(0)} 을 썼다. 원장에 없는 값이다.',
               REMEDIATION_ARBITRARY)

        for m in ARBITRARY_PROP_RE.finditer(text):
            if m.start() in variant_starts:
                continue
            at(m.start(), f'Tailwind 임의 속성 {m.group(0)} 을 썼다. 원장에 없는 값이다.',
               REMEDIATION_ARBITRARY)

        if rel.endswith(TSX_SUFFIXES):
            for m in INLINE_STYLE_RE.finditer(text):
                at(m.start(), '인라인 style={{...}} 을 썼다. 게이트가 볼 수 없는 자리다.',
                   REMEDIATION_INLINE_STYLE)

        for m in SPACING_RE.finditer(text):
            if m.group(2) not in SPACING_INDEX:
                at(m.start(),
                   f'여백 {m.group(1)}-{m.group(2)} 는 DESIGN.md spacing 9단 밖이다 '
                   f'(허용: {", ".join(sorted(SPACING_INDEX - {"auto", "px"}, key=float))}).',
                   REMEDIATION_SPACING)

        for m in DURATION_RE.finditer(text):
            at(m.start(),
               f'duration-{m.group(1)} 은 Tailwind 기본 스케일이다. '
               f'원장 변수를 참조하라 — duration-(--duration-fast) 또는 duration-(--duration-standard).',
               REMEDIATION_MOTION)

        for m in EASE_RE.finditer(text):
            if m.group(1) not in allowed_ease:
                at(m.start(), f'ease-{m.group(1)} 은 DESIGN.md motion 에 없다. ease-standard 를 쓰라.',
                   REMEDIATION_MOTION)

    return errors


# global.css 하나만 원장 CSS 로 본다 — check_theme/check_typography/check_motion/
# check_no_external_url 이 전부 이 파일 하나만 읽는다.
GLOBAL_CSS_PATH = 'src/app/global.css'


def check_no_extra_stylesheets(files):
    """global.css 외의 .css 파일이 app/ 또는 src/ 밑에 있으면 막는다(F2).

    scan_utilities 가 코드 파일(.ts/.tsx/.js/.jsx)만 보고 .css 를 스킵하는 판단, scan_code 가
    .css 안에서도 hex 리터럴만 보는 판단 둘 다 "global.css 가 유일한 스타일시트"라는 전제
    위에 있다. 그 전제를 강제하는 게 없으면 두 번째 스타일시트(예: CSS 모듈)는 spacing·
    motion·external-url 검사를 전부 피해간다. 스캔하는 대신 존재 자체를 막는다.
    """
    errors = []
    for rel, _ in files:
        if rel.endswith('.css') and rel != GLOBAL_CSS_PATH:
            errors.append(
                f"{rel}: 토큰 원장 CSS 는 {GLOBAL_CSS_PATH} 하나만 검사한다 — 이 두 번째 "
                f"스타일시트는 게이트가 검사하지 못하므로 허용하지 않는다. 스타일은 "
                f"{GLOBAL_CSS_PATH} 나 Tailwind 유틸리티 클래스로 옮겨라.")
    return errors


# 유틸리티의 원장 변수 참조 — duration-(--duration-fast), translate-y-(--hover-lift).
# 대괄호 임의값(ARBITRARY_RE)과 달리 이 괄호 문법은 원장을 가리키므로 허용해 왔다.
# 그런데 "가리킨다" 와 "실재한다" 는 다르다 — 없는 이름을 써도 Tailwind 는 var(--없는이름)
# 을 그대로 내보내고, 그 선언이 없으면 해당 속성이 조용히 무효가 된다. 오타 한 글자가
# 통과하고 스타일만 안 걸리는 자리다(실측: --duraiton-standard 로 바꿔도 게이트 OK).
# DESIGN.md §6 이 모션 값을 변수 직접 참조로 MUST 지정하므로 이 형태의 사용이 늘어난다.
VAR_REF_RE = re.compile(r'-\((--[\w-]+)\)')

# @theme 선언부. `--color-*: initial;` 리셋 라인은 `*` 가 [\w-] 밖이라 잡히지 않는다.
VAR_DECL_RE = re.compile(r'(--[\w-]+)\s*:')

REMEDIATION_VAR_REF = (
    '오타가 아닌지 먼저 확인하라 — src/app/global.css 의 @theme 선언과 한 글자씩 대조한다. '
    '없는 변수를 참조하면 그 속성이 조용히 무효가 되어 화면에 아무 변화가 없다. 정말 새 값이 '
    '필요하면 직접 추가하지 말고 사용자에게 물어라. global.css 는 편집 금지다.'
)


def check_var_refs(files, css):
    """코드가 참조하는 CSS 변수가 @theme 에 실재하는지 대조한다.

    .css 는 보지 않는다 — 선언부이고, var(--x) 사용은 declared 대조 대상이 아니다.
    Tailwind 내장 변수(--spacing 등)도 global.css 에 없으면 잡는다. 오탐이 아니라 의도다:
    원장에 없는 변수를 코드가 가리키는 것이 게이트가 막으려는 드리프트 그 자체다.
    """
    declared = set(VAR_DECL_RE.findall(css))
    errors = []
    for rel, text in files:
        if not rel.endswith(CODE_SUFFIXES):
            continue
        for m in VAR_REF_RE.finditer(text):
            name = m.group(1)
            if name in declared:
                continue
            near = difflib.get_close_matches(name, sorted(declared), n=1, cutoff=0.75)
            hint = f' {near[0]} 를 쓰려던 것인가?' if near else ''
            errors.append(
                f'{rel}:{_lineno(text, m.start())}: {name} 는 @theme 에 선언되지 않았다.{hint} '
                f'{REMEDIATION_VAR_REF}')
    return errors


# --- 컴포넌트 원장(SHARED-COMPONENTS.md) ------------------------------------
#
# 이 파일은 DESIGN.md 의 컴포넌트 영역이다. 값을 리터럴로 쓰면 그 순간 원장 밖 값이
# 되는데, 예전에는 아무도 안 봤다 — 실제로 "안쪽 p-4 · 행 간격 gap-1.5" 라는 원장에
# 없는 결정이 예시 블록에 박혀 있었다. 값을 토큰 참조({colors.accent})로 쓰게 형식을
# 바꿨으므로 이제 기계로 대조할 수 있다.

COMPONENT_LEDGER_PATH = 'SHARED-COMPONENTS.md'
COMPONENT_REF_RE = re.compile(r'\{([\w-]+)\.([\w.-]+)\}')
# frontmatter 에서 "키: 값" 이 같은 줄에 있는 항목만 본다. 부모 키(`card:`)는 값이 없다.
COMPONENT_ENTRY_RE = re.compile(r'^\s+([\w-]+):[ ]+(\S.*)$')
# 토큰으로 표현할 수 없는 CSS 키워드. 값이 아니라 "그 속성을 쓰지 않는다"는 선언이다.
COMPONENT_LITERAL_OK = frozenset({'none', 'transparent'})

REMEDIATION_COMPONENT_REF = (
    'DESIGN.md 에 있는 토큰 이름으로 바꿔라. 원장에 없는 값이 필요하면 여기에 직접 적지 '
    '말고 DESIGN.proposed.yaml 에 근거와 함께 등록한다.'
)
REMEDIATION_COMPONENT_LITERAL = (
    f'리터럴 대신 토큰 참조로 써라 — 예: {{colors.accent}}. {COMPONENT_LEDGER_PATH} 는 '
    'DESIGN.md 토큰을 조립하는 곳이지 새 값을 정하는 곳이 아니다. 값 자체가 필요하면 '
    'DESIGN.proposed.yaml 로 간다.'
)


def _component_frontmatter(text):
    """--- 로 감싼 첫 블록. 없으면 None."""
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    return m.group(1) if m else None


def check_component_refs(text, families):
    """컴포넌트 원장의 값이 전부 실재하는 토큰 참조인지 대조한다.

    families: {계열: {토큰 이름}} — ledger.ledger_families() 가 만든다.
    frontmatter 가 없으면 검사할 것이 없으므로 조용히 통과한다.
    """
    fm = _component_frontmatter(text)
    if fm is None:
        return []

    errors = []
    for i, line in enumerate(fm.splitlines(), start=2):  # 1행은 여는 ---
        m = COMPONENT_ENTRY_RE.match(line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        val = raw.strip("'\"")
        if val in COMPONENT_LITERAL_OK:
            continue
        ref = COMPONENT_REF_RE.fullmatch(val)
        if not ref:
            errors.append(
                f'{COMPONENT_LEDGER_PATH}:{i}: {key} 의 값 {raw} 이 토큰 참조가 아니다. '
                f'{REMEDIATION_COMPONENT_LITERAL}')
            continue
        fam, tok = ref.group(1), ref.group(2)
        if fam not in families:
            errors.append(
                f'{COMPONENT_LEDGER_PATH}:{i}: {{{fam}.{tok}}} 의 계열 {fam} 이 원장에 없다 '
                f'(있는 계열: {", ".join(sorted(families))}). {REMEDIATION_COMPONENT_REF}')
        elif tok not in families[fam]:
            near = difflib.get_close_matches(tok, sorted(families[fam]), n=1, cutoff=0.7)
            hint = f' {{{fam}.{near[0]}}} 를 쓰려던 것인가?' if near else ''
            errors.append(
                f'{COMPONENT_LEDGER_PATH}:{i}: {{{fam}.{tok}}} 는 DESIGN.md {fam} 에 없다.'
                f'{hint} {REMEDIATION_COMPONENT_REF}')
    return errors


def unwired_proposed(proposed, css):
    """제안층에 등록됐으나 @theme 에 아직 없는 색. 에러가 아니라 통지다.

    등록(제안층)과 배선(@theme)은 다른 사람이 한다 — 에이전트는 제안층까지 쓸 수 있지만
    global.css 는 잠겨 있어 사람이 넣어야 한다. 이 시차를 에러로 잡으면 등록하는 순간부터
    그 색과 무관한 작업까지 전부 커밋이 막힌다. 코드가 실제로 그 색을 쓰면 scan_code 가
    막으므로, 여기서는 "아직 쓸 수 없다"고 알리기만 한다.
    """
    wired = set(re.findall(r'--color-([\w-]+):', css))
    return sorted(set(proposed) - wired)


# check_theme 이 제안층 미배선을 에러에서 뺀 대가로 생기는 구멍을 막는다. 등록만 하고
# @theme 에 없는 색을 코드가 쓰면(bg-info) Tailwind 는 그 유틸리티를 아예 만들지 않는다 —
# 에러도 없고 스타일도 없다. 완화가 안전하려면 "등록은 통과, 사용은 차단"이어야 한다.
COLOR_UTIL_PREFIX = (
    'bg|text|border|outline|ring|divide|fill|stroke|decoration'
    '|from|via|to|accent|caret|placeholder|shadow')

REMEDIATION_UNWIRED_USE = (
    '@theme 에 없는 색은 Tailwind 가 유틸리티를 만들지 않아 아무 스타일도 걸리지 않는다. '
    'src/app/global.css 에 --color-<이름> 이 추가될 때까지는 확정층 색을 쓰고, 추가는 '
    '직접 하지 말고 사용자에게 요청하라.'
)


def check_unwired_usage(files, unwired):
    """@theme 에 아직 없는 제안층 색을 코드가 쓰고 있으면 막는다."""
    if not unwired:
        return []
    pattern = re.compile(
        rf'\b(?:{COLOR_UTIL_PREFIX})'
        rf'(?:-(?:t|r|b|l|s|e|x|y|top|right|bottom|left|inline|block|offset))?'
        rf'-({"|".join(re.escape(n) for n in sorted(unwired))})\b')
    errors = []
    for rel, text in files:
        if not rel.endswith(CODE_SUFFIXES):
            continue
        for m in pattern.finditer(text):
            errors.append(
                f'{rel}:{_lineno(text, m.start())}: {m.group(0)} 를 썼으나 {m.group(1)} 은 '
                f'제안층에만 있고 @theme 에 없다. {REMEDIATION_UNWIRED_USE}')
    return errors
