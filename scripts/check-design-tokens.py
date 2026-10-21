#!/usr/bin/env python3
# scripts/check-design-tokens.py
"""토큰 무결성 게이트.

확정층(DESIGN.md) · 제안층(DESIGN.proposed.yaml) · @theme · 앱 코드를 대조한다.
3분기: 확정층 통과 / 제안층 통과+집계 / 미등록 차단.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from design_tokens import checks, ledger  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROOT_CSS = 'src/app/global.css'
SCAN_DIRS = ('app', 'src')
SCAN_SUFFIXES = ('.ts', '.tsx', '.css', '.js', '.jsx')


def collect_files():
    out = []
    for base in SCAN_DIRS:
        d = ROOT / base
        if not d.exists():
            continue
        for f in sorted(d.rglob('*')):
            if f.is_file() and f.suffix in SCAN_SUFFIXES:
                out.append((str(f.relative_to(ROOT)), f.read_text(encoding='utf-8')))
    return out


def main():
    design_md = (ROOT / 'DESIGN.md').read_text(encoding='utf-8')
    confirmed = ledger.parse_confirmed(design_md)
    shape = ledger.parse_shape(design_md)

    if not confirmed:
        print('DESIGN.md 에서 colors 를 읽지 못했다 — frontmatter 형식을 확인하라')
        return 1

    errors = ledger.validate_confirmed(confirmed)
    errors += ledger.validate_block_origins(design_md)
    proposed_path = ROOT / 'DESIGN.proposed.yaml'
    proposed_text = proposed_path.read_text(encoding='utf-8') if proposed_path.exists() else ''
    proposed = ledger.parse_proposed(proposed_text)
    errors += ledger.validate_proposed(proposed, confirmed)

    # 반려(rejected)된 제안은 통과 대상에서 뺀다 — 그 값을 여전히 쓰는 코드/@theme 는
    # 아래 두 검사에서 반려 사실을 명시해 차단한다. rejected 외 상태는 전부 활성으로 본다.
    active = ledger.active_proposed(proposed)
    rejected = ledger.rejected_proposed(proposed)

    css = (ROOT / 'src' / 'app' / 'global.css').read_text(encoding='utf-8')
    errors += checks.check_theme(confirmed, active, shape, css, rejected=rejected)
    errors += checks.check_typography(
        ledger.parse_typography(design_md), ledger.parse_hangul_tracking(design_md), css)
    errors += checks.check_font_stacks(ledger.parse_font_stacks(design_md), css)
    errors += checks.check_motion(ledger.parse_motion(design_md), css)
    errors += checks.check_no_external_url(css)

    allowed = {v['value'] for v in confirmed.values()} | {v['value'] for v in active.values()}
    files = collect_files()
    errors += checks.check_no_extra_stylesheets(files)
    errors += checks.scan_code(allowed, files, rejected=rejected)
    errors += checks.scan_utilities(files)
    errors += checks.check_var_refs(files, css)

    errors += checks.check_unwired_usage(files, checks.unwired_proposed(active, css))

    component_path = ROOT / checks.COMPONENT_LEDGER_PATH
    if component_path.exists():
        errors += checks.check_component_refs(
            component_path.read_text(encoding='utf-8'),
            ledger.ledger_families(design_md, confirmed, active, shape))

    if errors:
        print('\n'.join(errors))
        return 1
    pending = ledger.pending_proposed(proposed)
    unwired = checks.unwired_proposed(active, css)
    if pending:
        print(f'OK — 제안층 pending {len(pending)}건')
        for name, meta in pending:
            print(f"  {name}({meta['value']}) {meta['by']}, {meta['added']} — {meta['rationale']}")
    else:
        print('OK')
    if unwired:
        # 붙여넣을 줄을 그대로 찍는다. 이 안내를 읽는 사람은 기획자이고 잠금 때문에
        # 에이전트가 대신 넣어줄 수 없다 — "--color-<이름> 을 추가하라"는 설명보다
        # 복사할 수 있는 한 줄이 낫다.
        print(f"\n아직 @theme 에 없어 코드에서 쓸 수 없는 제안 {len(unwired)}건: "
              f"{', '.join(unwired)}")
        print(f"  {ROOT_CSS} 의 @theme {{ ... }} 블록 안에 아래 줄을 그대로 추가하세요:")
        for name in unwired:
            print(f"      --color-{name}: {active[name]['value']};")
        print('  잠금 영역이라 사람이 직접 넣습니다 — 절차는 docs/maintenance.md 에 있다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
