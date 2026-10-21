"""DESIGN.md / DESIGN.proposed.yaml 파싱 — 순수 함수만 둔다."""
import re

VALID_ORIGINS = {'brandbook', 'derived', 'product'}

# 색 외 블록은 블록 단위로 출처를 단다(`origin: product`). colors 는 토큰 단위라 빠진다.
# 한 블록 안에 출처가 섞이면 그 블록은 brandbook 이 아니다 — 블록 단위로 product 를 단다.
ORIGIN_BLOCKS = ('rounded', 'borders', 'shadows', 'spacing', 'typography',
                 'fontFamilies', 'hangulTracking', 'motion', 'breakpoints')
# 블록 메타 키. 토큰 이름으로 읽으면 안 된다.
BLOCK_META_KEYS = frozenset({'origin', 'since'})


def _frontmatter(text):
    """--- 로 감싼 첫 블록을 돌려준다. 없으면 빈 문자열."""
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    return m.group(1) if m else ''


def _block(fm, name):
    """`name:` 아래 들여쓴 줄들을 돌려준다."""
    m = re.search(rf'^{re.escape(name)}:\n((?:  .*\n)+)', fm + '\n', re.M)
    return m.group(1) if m else ''


def _named_values(fm, name):
    """`  key: 'value'` 줄을 {key: value} 로 돌려준다. 블록 메타 키는 뺀다."""
    pairs = re.findall(r"^  ([\w-]+): '([^']+)'", _block(fm, name), re.M)
    return {k: v for k, v in pairs if k not in BLOCK_META_KEYS}


def parse_confirmed(text):
    """확정층 색을 {name: {value, origin, since}} 로 돌려준다."""
    out = {}
    for line in _block(_frontmatter(text), 'colors').splitlines():
        m = re.match(r"\s+([\w-]+):\s*\{\s*value:\s*'(#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?)'"
                     r"\s*,\s*origin:\s*(\w+)\s*(?:,\s*since:\s*'([^']+)'\s*)?\}", line)
        if m:
            out[m.group(1)] = {
                'value': m.group(2).upper(),
                'origin': m.group(3),
                'since': m.group(4),
            }
    return out


def parse_shape(text):
    """모양 토큰을 돌려준다."""
    fm = _frontmatter(text)
    rounded = _named_values(fm, 'rounded')
    shadow = re.search(r"^  extruded: '([^']+)'", _block(fm, 'shadows'), re.M)
    bp = re.search(r"^  mobile-max: '([^']+)'", _block(fm, 'breakpoints'), re.M)
    return {
        'rounded': rounded,
        'shadow_extruded': shadow.group(1) if shadow else None,
        'mobile_max': bp.group(1) if bp else None,
    }


def validate_confirmed(confirmed):
    """확정층 자체의 무결성을 검사한다."""
    errors = []
    for name, meta in sorted(confirmed.items()):
        if meta['origin'] not in VALID_ORIGINS:
            errors.append(f"DESIGN.md colors.{name}: 알 수 없는 origin '{meta['origin']}' "
                          f"(허용: {', '.join(sorted(VALID_ORIGINS))})")
        if meta['origin'] in ('product', 'derived') and not meta['since']:
            errors.append(f"DESIGN.md colors.{name}: origin={meta['origin']} 은 since 가 필수다")
        if meta['value'].startswith(('#FFFFFF', '#000000')):
            errors.append(f"DESIGN.md colors.{name}: 순수 화이트·검정은 팔레트에 둘 수 없다")
    return errors


PROPOSED_REQUIRED = ('value', 'added', 'by', 'rationale', 'status')


def validate_block_origins(text):
    """색 외 블록마다 `origin:` 이 있고 허용 값인지 검사한다.

    since 는 블록 단위에서 선택이다 — 블록 출처는 값이 생긴 뒤에 분류했으므로 도입 날짜를
    모르는 블록이 있다. 블록 자체가 없으면 여기서는 넘어간다(각 블록 검사가 잡는다).
    """
    fm = _frontmatter(text)
    errors = []
    for name in ORIGIN_BLOCKS:
        blk = _block(fm, name)
        if not blk:
            continue
        m = re.search(r'^  origin:\s*(\S+)\s*$', blk, re.M)
        if not m:
            errors.append(f"DESIGN.md {name}: 블록 출처(origin)가 없다 — 블록 안에 "
                          f"'origin: product' 처럼 단다. 브랜드북 값만으로 된 블록만 brandbook 이다")
        elif m.group(1) not in VALID_ORIGINS:
            errors.append(f"DESIGN.md {name}: 알 수 없는 origin '{m.group(1)}' "
                          f"(허용: {', '.join(sorted(VALID_ORIGINS))})")
    return errors


def parse_proposed(text):
    """제안층을 {name: {value, added, by, rationale, status}} 로 돌려준다.

    2단 들여쓰기 매핑만 지원한다 — 제안층은 이 형식만 쓴다.
    """
    out = {}
    current = None
    in_colors = False
    for line in text.splitlines():
        if re.match(r'^colors:\s*$', line):
            in_colors = True
            continue
        if in_colors and re.match(r'^\S', line):
            in_colors = False
        if not in_colors:
            continue
        m_name = re.match(r'^  ([\w-]+):\s*$', line)
        if m_name:
            current = m_name.group(1)
            out[current] = {}
            continue
        m_kv = re.match(r"^    (\w+):\s*'?([^'\n]*?)'?\s*$", line)
        if m_kv and current:
            key, val = m_kv.group(1), m_kv.group(2)
            out[current][key] = val.upper() if key == 'value' else val
    return out


def validate_proposed(proposed, confirmed=None):
    """제안층 항목이 근거를 갖췄는지, 확정층과 겹치지 않는지 검사한다."""
    errors = []
    confirmed = confirmed or {}
    for name, meta in sorted(proposed.items()):
        for field in PROPOSED_REQUIRED:
            # strip 후 검사 — 공백만 있는 값은 "값이 있다"고 치지 않는다. rationale 이
            # 근거로 기능하려면 공백은 미기재와 같은 취급을 받아야 한다.
            if not (meta.get(field) or '').strip():
                errors.append(
                    f"DESIGN.proposed.yaml colors.{name}: '{field}' 가 없다. "
                    f"제안 토큰은 {', '.join(PROPOSED_REQUIRED)} 를 모두 채워야 한다")
        if name in confirmed:
            errors.append(
                f"DESIGN.proposed.yaml colors.{name}: 확정층에 이미 있는 이름이다. "
                f"확정층 값을 쓰거나 다른 이름을 골라라")
        value = (meta.get('value') or '').upper()
        if value.startswith(('#FFFFFF', '#000000')):
            errors.append(
                f"DESIGN.proposed.yaml colors.{name}: 순수 화이트·검정은 팔레트에 둘 수 없다")
    return errors


def active_proposed(proposed):
    """제안층에서 반려(rejected)되지 않은 항목만 돌려준다.

    'rejected' 외의 상태(예: pending, 그 밖의 값)는 전부 활성으로 취급한다 — 승격/반려
    2단계를 넘는 워크플로 상태 기계는 이 게이트의 범위 밖이다.
    """
    return {n: m for n, m in proposed.items() if m.get('status') != 'rejected'}


def rejected_proposed(proposed):
    """제안층에서 반려된 항목만 {name: meta} 로 돌려준다."""
    return {n: m for n, m in proposed.items() if m.get('status') == 'rejected'}


def pending_proposed(proposed):
    """제안층에서 승격 심사 리포트에 낼 pending 항목만 (name, meta) 목록으로 돌려준다."""
    return sorted((n, m) for n, m in proposed.items() if m.get('status') == 'pending')


TYPO_TOKENS = ('headline', 'subhead', 'body-head', 'body-large',
               'body', 'body-small', 'label', 'label-small')


def parse_typography(text):
    """타이포 토큰을 {name: {...}} 로 돌려준다."""
    fm = _frontmatter(text)
    out = {}
    for line in _block(fm, 'typography').splitlines():
        m = re.match(r'\s+([\w-]+):\s*\{(.+)\}\s*$', line)
        if not m:
            continue
        name, body = m.group(1), m.group(2)

        def pick(pattern):
            mm = re.search(pattern, body)
            return mm.group(1) if mm else None

        responsive = re.search(
            r"fontSize: \{ pc: '([\d.]+rem)', mobile: '([\d.]+rem)' \}", body)
        out[name] = {
            'fontFamily': pick(r"fontFamily: '([^']+)'"),
            'fontWeight': pick(r'fontWeight: (\d+)'),
            'fontSize': pick(r"fontSize: '([\d.]+rem)'"),
            'fontSizeResponsive': (responsive.group(1), responsive.group(2)) if responsive else None,
            'letterSpacing': pick(r"letterSpacing: '(-?[\d.]+em|0)'"),
            'lineHeight': pick(r"lineHeight: '(\d+%)'"),
            'uppercase': 'textTransform: uppercase' in body,
        }
    return out


def parse_font_stacks(text):
    """{'maru': stack, 'inter': stack} 을 돌려준다."""
    return dict(re.findall(r'^  stack-(maru|inter): "([^"]+)"',
                           _block(_frontmatter(text), 'fontFamilies'), re.M))


def parse_hangul_tracking(text):
    """한글 자간 예외를 돌려준다."""
    blk = _block(_frontmatter(text), 'hangulTracking')
    scope = re.search(r'scope: "([^"]+)"', blk)
    ls = re.search(r"letterSpacing: '([^']+)'", blk)
    tokens = re.search(r"tokens: '([^']+)'", blk)
    return {
        'scope': scope.group(1) if scope else None,
        'letterSpacing': ls.group(1) if ls else None,
        'tokens': [t.strip() for t in tokens.group(1).split(',')] if tokens else [],
    }


def parse_motion(text):
    """모션 토큰을 {name: value} 로 돌려준다."""
    return _named_values(_frontmatter(text), 'motion')


def parse_borders(text):
    """테두리 폭 토큰을 돌려준다."""
    return _named_values(_frontmatter(text), 'borders')


# spacing.scale 은 순서 있는 배열이라 이름이 없다. 코드가 쓰는 Tailwind 단계 표기를
# 키로 삼는다 — 1=4px 1.5=6px 2=8px 3=12px 4=16px 6=24px 8=32px 12=48px 16=64px.
# 이 표기는 CLAUDE.md 와 checks.SPACING_INDEX 가 이미 쓰는 것이라 새로 만든 규약이 아니다.
SPACING_STEPS = ('1', '1.5', '2', '3', '4', '6', '8', '12', '16')


def ledger_families(design_md, confirmed, active, shape):
    """컴포넌트 원장이 참조할 수 있는 토큰 이름을 계열별로 모은다."""
    return {
        'colors': set(confirmed) | set(active),
        'rounded': set(shape['rounded']),
        'borders': set(parse_borders(design_md)),
        'shadows': {'extruded'} if shape['shadow_extruded'] else set(),
        'typography': set(parse_typography(design_md)),
        'motion': set(parse_motion(design_md)),
        'spacing': set(SPACING_STEPS),
    }
