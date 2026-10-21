import importlib.util
import pathlib
import unittest
from design_tokens import ledger, checks

# check-design-tokens.py 는 하이픈이 들어간 파일명이라 일반 import 문으로는 못 불러온다 —
# importlib 로 경로 기반 로드. main() 은 __main__ 가드 안에 있어 import 시 실행되지 않는다.
_GATE_PATH = pathlib.Path(__file__).resolve().parent / 'check-design-tokens.py'
_gate_spec = importlib.util.spec_from_file_location('check_design_tokens_gate', _GATE_PATH)
gate = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(gate)

CONFIRMED_FM = """---
colors:
  accent:  { value: '#24F351', origin: brandbook }
  danger:  { value: '#C41E1E', origin: product, since: '2026-08-05' }
rounded:
  small: '10px'
  card: '24px'
  pill: '999px'
shadows:
  extruded: '4px 5px 0 #070707'
breakpoints:
  mobile-max: '768px'
---
# 본문
"""


class ParseConfirmedTest(unittest.TestCase):
    def test_색과_origin을_읽는다(self):
        got = ledger.parse_confirmed(CONFIRMED_FM)
        self.assertEqual(got['accent'], {'value': '#24F351', 'origin': 'brandbook', 'since': None})
        self.assertEqual(got['danger'], {'value': '#C41E1E', 'origin': 'product', 'since': '2026-08-05'})

    def test_소문자_hex를_대문자로_정규화한다(self):
        got = ledger.parse_confirmed("---\ncolors:\n  a: { value: '#abcdef', origin: brandbook }\n---\n")
        self.assertEqual(got['a']['value'], '#ABCDEF')


class ValidateConfirmedTest(unittest.TestCase):
    def test_순수_검정_ledger_항목을_차단한다(self):
        confirmed = ledger.parse_confirmed(
            "---\ncolors:\n  a: { value: '#000000', origin: brandbook }\n---\n")
        errs = ledger.validate_confirmed(confirmed)
        self.assertTrue(any('a' in e and ('화이트' in e or '검정' in e) for e in errs))

    def test_순수_화이트_ledger_항목도_여전히_차단한다(self):
        confirmed = ledger.parse_confirmed(
            "---\ncolors:\n  a: { value: '#FFFFFF', origin: brandbook }\n---\n")
        errs = ledger.validate_confirmed(confirmed)
        self.assertTrue(any('a' in e and ('화이트' in e or '검정' in e) for e in errs))


class ParseShapeTest(unittest.TestCase):
    def test_모양_토큰을_읽는다(self):
        got = ledger.parse_shape(CONFIRMED_FM)
        self.assertEqual(got['rounded'], {'small': '10px', 'card': '24px', 'pill': '999px'})
        self.assertEqual(got['shadow_extruded'], '4px 5px 0 #070707')
        self.assertEqual(got['mobile_max'], '768px')


# 색 외 블록은 블록 단위로 출처를 단다. 모든 블록이 아래 형태를 갖춘 원장.
BLOCK_ORIGIN_FM = """---
colors:
  accent:  { value: '#24F351', origin: brandbook }
rounded:
  origin: product
  since: '2026-10-20'
  small: '10px'
borders:
  origin: product
  hairline: '1px'
shadows:
  origin: product
  extruded: '4px 5px 0 #070707'
spacing:
  scale: ['4px']
  origin: product
  since: '2026-08-14'
typography:
  origin: product
  body: { fontFamily: 'Inter', fontWeight: 400, fontSize: '1rem', letterSpacing: '0', lineHeight: '123%' }
fontFamilies:
  origin: product
  latin-text: 'Inter'
hangulTracking:
  origin: product
  scope: "html[lang='ko']"
motion:
  origin: product
  since: '2026-10-20'
  duration-fast: '150ms'
breakpoints:
  origin: product
  mobile-max: '768px'
---
"""


class BlockOriginTest(unittest.TestCase):
    def test_모든_블록에_출처가_있으면_통과한다(self):
        self.assertEqual(ledger.validate_block_origins(BLOCK_ORIGIN_FM), [])

    def test_출처가_없는_블록을_잡는다(self):
        text = BLOCK_ORIGIN_FM.replace('motion:\n  origin: product\n', 'motion:\n')
        errs = ledger.validate_block_origins(text)
        self.assertEqual(len(errs), 1)
        self.assertIn('motion', errs[0])

    def test_알_수_없는_출처를_잡는다(self):
        text = BLOCK_ORIGIN_FM.replace('rounded:\n  origin: product', 'rounded:\n  origin: figma')
        errs = ledger.validate_block_origins(text)
        self.assertTrue(any('rounded' in e and 'figma' in e for e in errs))

    def test_블록이_통째로_없으면_여기서는_잡지_않는다(self):
        """블록 누락은 각 블록 검사(check_motion 등)의 몫이다. 여기서 또 내면 같은 원인에
        메시지가 두 번 뜬다."""
        text = BLOCK_ORIGIN_FM.replace("hangulTracking:\n  origin: product\n  scope: \"html[lang='ko']\"\n", '')
        self.assertEqual(ledger.validate_block_origins(text), [])

    def test_출처_줄은_토큰으로_읽히지_않는다(self):
        """origin·since 는 블록 메타다. 토큰으로 읽히면 @theme 대조에서 --radius-since 같은
        없는 변수를 요구하게 된다."""
        self.assertEqual(ledger.parse_shape(BLOCK_ORIGIN_FM)['rounded'], {'small': '10px'})
        self.assertEqual(ledger.parse_motion(BLOCK_ORIGIN_FM), {'duration-fast': '150ms'})
        self.assertEqual(ledger.parse_borders(BLOCK_ORIGIN_FM), {'hairline': '1px'})
        self.assertEqual(set(ledger.parse_typography(BLOCK_ORIGIN_FM)), {'body'})


class ScanCodeTest(unittest.TestCase):
    def test_팔레트_색은_통과한다(self):
        errs = checks.scan_code({'#24F351'}, [('src/pages/a.tsx', 'const c = "#24F351";')])
        self.assertEqual(errs, [])

    def test_미등록_hex는_차단한다(self):
        errs = checks.scan_code({'#24F351'}, [('src/pages/a.tsx', 'const c = "#3B82F6";')])
        self.assertEqual(len(errs), 1)
        self.assertIn('#3B82F6', errs[0])
        self.assertIn('src/pages/a.tsx', errs[0])

    def test_순수_화이트_hex를_차단한다(self):
        errs = checks.scan_code({'#24F351'}, [('src/pages/a.tsx', 'color: #FFF;')])
        self.assertTrue(any('화이트' in e for e in errs))

    def test_화이트_검정_유틸리티를_차단한다(self):
        errs = checks.scan_code({'#24F351'}, [('src/pages/a.tsx', '<div className="bg-white text-black" />')])
        self.assertTrue(any('bg-white' in e for e in errs))
        self.assertTrue(any('text-black' in e for e in errs))

    def test_방향성_오프셋_화이트_검정_유틸리티를_차단한다(self):
        errs = checks.scan_code({'#24F351'}, [('src/pages/a.tsx',
            '<div className="border-t-white ring-offset-white divide-y-black" />')])
        self.assertTrue(any('border-t-white' in e for e in errs))
        self.assertTrue(any('ring-offset-white' in e for e in errs))
        self.assertTrue(any('divide-y-black' in e for e in errs))


class ScanCodeMessageContractTest(unittest.TestCase):
    """F3 — 스킴 §4.2 이 요구하는 형태: file:line + 교정 지시문."""

    def test_원장에_없는_색_메시지에_줄번호와_교정문구가_있다(self):
        text = 'const a = 1;\nconst b = 2;\nconst c = "#3B82F6";\n'
        errs = checks.scan_code(set(), [('src/pages/cart.tsx', text)])
        self.assertEqual(len(errs), 1)
        self.assertIn('src/pages/cart.tsx:3', errs[0])
        self.assertIn('#3B82F6', errs[0])
        self.assertIn('직접 추가하지 말고 사용자에게 물어라', errs[0])

    def test_순수_화이트_메시지에도_줄번호와_교정문구가_있다(self):
        text = 'const a = 1;\ncolor: #FFF;\n'
        errs = checks.scan_code({'#24F351'}, [('src/pages/cart.tsx', text)])
        white_errs = [e for e in errs if '화이트' in e]
        self.assertEqual(len(white_errs), 1)
        self.assertIn('src/pages/cart.tsx:2', white_errs[0])
        self.assertIn('직접 추가하지 말고 사용자에게 물어라', white_errs[0])

    def test_화이트_검정_유틸리티_메시지에도_줄번호와_교정문구가_있다(self):
        text = 'const a = 1;\n<div className="bg-white" />\n'
        errs = checks.scan_code({'#24F351'}, [('src/pages/cart.tsx', text)])
        util_errs = [e for e in errs if 'bg-white' in e]
        self.assertEqual(len(util_errs), 1)
        self.assertIn('src/pages/cart.tsx:2', util_errs[0])
        self.assertIn('직접 추가하지 말고 사용자에게 물어라', util_errs[0])

    def test_반려_토큰_메시지는_건드리지_않는다(self):
        """반려 토큰 메시지는 이미 올바르다 — F3 이 손대지 않는다(회귀 확인)."""
        rejected = {'info': {'value': '#2D7FF9'}}
        errs = checks.scan_code(set(), [('src/pages/a.tsx', '"#2D7FF9"')], rejected=rejected)
        self.assertEqual(len(errs), 1)
        self.assertIn('반려된 제안 토큰', errs[0])
        self.assertNotIn(':1:', errs[0])


class CheckThemeTest(unittest.TestCase):
    CSS_OK = """@theme {
  --color-*: initial;
  --radius-*: initial;
  --color-accent: #24F351;
  --color-danger: #C41E1E;
  --radius-small: 10px;
  --radius-card: 24px;
  --radius-pill: 999px;
  --shadow-extruded: 4px 5px 0 #070707;
}"""

    def test_일치하면_에러가_없다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        self.assertEqual(checks.check_theme(confirmed, {}, shape, self.CSS_OK), [])

    def test_theme에_없는_원장_색을_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS_OK.replace('  --color-danger: #C41E1E;\n', '')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('danger' in e for e in errs))

    def test_값_드리프트를_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS_OK.replace('#24F351', '#24F352')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('accent' in e for e in errs))

    def test_원장에_없는_radius를_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS_OK.replace('}', '  --radius-xl: 40px;\n}')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('radius-xl' in e for e in errs))

    def test_원장에_없는_shadow를_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS_OK.replace('}', "  --shadow-glow: 0 0 10px #FFFFFF;\n}")
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('shadow-glow' in e for e in errs))

    def test_radius_reset_라인은_보고하지_않는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS_OK.replace('@theme {', "@theme {\n  --radius-*: initial;")
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertEqual(errs, [])


class CheckThemeNonHexColorTest(unittest.TestCase):
    """F1 — hex 가 아닌 --color-* 값도 등식 불변식에 들어와야 한다."""

    def test_oklch_색_값은_hex가_아니라고_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = CheckThemeTest.CSS_OK.replace('}', "  --color-brandnew: oklch(0.6 0.2 250);\n}")
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('brandnew' in e and 'hex' in e for e in errs))

    def test_rgb_색_값은_hex가_아니라고_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = CheckThemeTest.CSS_OK.replace('}', "  --color-brandnew: rgb(59 130 246);\n}")
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('brandnew' in e and 'hex' in e for e in errs))

    def test_color_reset_라인은_hex_검사에도_안_걸린다(self):
        """--color-*: initial; 은 '*' 가 [\\w-] 밖이라 애초에 캡처되지 않는다."""
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = CheckThemeTest.CSS_OK.replace('@theme {', "@theme {\n  --color-*: initial;")
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertEqual(errs, [])

    def test_기존_hex_일치_케이스는_여전히_통과한다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        self.assertEqual(checks.check_theme(confirmed, {}, shape, CheckThemeTest.CSS_OK), [])


class ThemeResetGuardTest(unittest.TestCase):
    """F2 — --color-*/--radius-* 리셋 라인이 지워지면 Tailwind 기본 팔레트가 되살아난다."""

    def test_color_reset_누락을_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = CheckThemeTest.CSS_OK.replace('  --color-*: initial;\n', '')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('--color-*' in e and 'initial' in e for e in errs))

    def test_radius_reset_누락을_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = CheckThemeTest.CSS_OK.replace('  --radius-*: initial;\n', '')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('--radius-*' in e and 'initial' in e for e in errs))

    def test_둘_다_있으면_리셋_관련_에러가_없다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        errs = checks.check_theme(confirmed, {}, shape, CheckThemeTest.CSS_OK)
        self.assertFalse(any('initial' in e for e in errs))


PROPOSED_OK = """colors:
  info:
    value: '#2D7FF9'
    added: '2026-09-01'
    by: '기획'
    rationale: '주문 상태 안내 배지 — 기존 팔레트에 중립 정보색 없음'
    status: pending
"""

PROPOSED_NO_RATIONALE = """colors:
  info:
    value: '#2D7FF9'
    added: '2026-09-01'
    by: '기획'
    status: pending
"""


class ParseProposedTest(unittest.TestCase):
    def test_제안_토큰을_읽는다(self):
        got = ledger.parse_proposed(PROPOSED_OK)
        self.assertEqual(got['info']['value'], '#2D7FF9')
        self.assertEqual(got['info']['by'], '기획')
        self.assertEqual(got['info']['status'], 'pending')

    def test_빈_문자열은_빈_dict다(self):
        self.assertEqual(ledger.parse_proposed(''), {})


class ValidateProposedTest(unittest.TestCase):
    def test_필수_필드가_있으면_통과한다(self):
        self.assertEqual(ledger.validate_proposed(ledger.parse_proposed(PROPOSED_OK)), [])

    def test_rationale_누락을_잡는다(self):
        errs = ledger.validate_proposed(ledger.parse_proposed(PROPOSED_NO_RATIONALE))
        self.assertEqual(len(errs), 1)
        self.assertIn('rationale', errs[0])
        self.assertIn('info', errs[0])

    def test_확정층과_이름이_겹치면_잡는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        proposed = ledger.parse_proposed(
            "colors:\n  accent:\n    value: '#2D7FF9'\n    added: '2026-09-01'\n"
            "    by: '기획'\n    rationale: 'x'\n    status: pending\n")
        errs = ledger.validate_proposed(proposed, confirmed)
        self.assertTrue(any('accent' in e and '확정층' in e for e in errs))


class ThreeWayTest(unittest.TestCase):
    def test_제안층_색은_코드에서_통과한다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        proposed = ledger.parse_proposed(PROPOSED_OK)
        allowed = ({v['value'] for v in confirmed.values()}
                   | {v['value'] for v in proposed.values()})
        self.assertEqual(checks.scan_code(allowed, [('src/pages/a.tsx', '"#2D7FF9"')]), [])

    def test_어디에도_없는_색은_차단한다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        proposed = ledger.parse_proposed(PROPOSED_OK)
        allowed = ({v['value'] for v in confirmed.values()}
                   | {v['value'] for v in proposed.values()})
        errs = checks.scan_code(allowed, [('src/pages/a.tsx', '"#ABCDEF"')])
        self.assertEqual(len(errs), 1)


PROPOSED_BLANK_RATIONALE = """colors:
  info:
    value: '#2D7FF9'
    added: '2026-09-01'
    by: '기획'
    rationale: ' '
    status: pending
"""

PROPOSED_WHITE = """colors:
  paper:
    value: '#FFFFFF'
    added: '2026-09-01'
    by: '기획'
    rationale: 'x'
    status: pending
"""

PROPOSED_BLACK = """colors:
  ink:
    value: '#000000'
    added: '2026-09-01'
    by: '기획'
    rationale: 'x'
    status: pending
"""

PROPOSED_REJECTED = """colors:
  info:
    value: '#2D7FF9'
    added: '2026-09-01'
    by: '기획'
    rationale: '반려 확인용'
    status: rejected
"""


class ValidateProposedFieldQualityTest(unittest.TestCase):
    def test_공백뿐인_rationale을_잡는다(self):
        errs = ledger.validate_proposed(ledger.parse_proposed(PROPOSED_BLANK_RATIONALE))
        self.assertEqual(len(errs), 1)
        self.assertIn('rationale', errs[0])
        self.assertIn('info', errs[0])

    def test_순수_화이트_제안을_잡는다(self):
        errs = ledger.validate_proposed(ledger.parse_proposed(PROPOSED_WHITE))
        self.assertTrue(any('paper' in e and ('화이트' in e or '검정' in e) for e in errs))

    def test_순수_검정_제안을_잡는다(self):
        errs = ledger.validate_proposed(ledger.parse_proposed(PROPOSED_BLACK))
        self.assertTrue(any('ink' in e and ('화이트' in e or '검정' in e) for e in errs))


class RejectedProposedTest(unittest.TestCase):
    def test_반려된_토큰은_active_제안에서_빠진다(self):
        proposed = ledger.parse_proposed(PROPOSED_REJECTED)
        active = ledger.active_proposed(proposed)
        self.assertNotIn('info', active)

    def test_pending_토큰은_active_제안에_남는다(self):
        proposed = ledger.parse_proposed(PROPOSED_OK)
        active = ledger.active_proposed(proposed)
        self.assertIn('info', active)

    def test_반려된_토큰은_pending_리포트에_안_잡힌다(self):
        proposed = ledger.parse_proposed(PROPOSED_REJECTED)
        self.assertEqual(ledger.pending_proposed(proposed), [])

    def test_pending_토큰은_pending_리포트에_잡힌다(self):
        proposed = ledger.parse_proposed(PROPOSED_OK)
        pending = ledger.pending_proposed(proposed)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0][0], 'info')

    def test_반려된_토큰의_색을_코드에서_쓰면_반려_사실을_명시해_차단한다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        proposed = ledger.parse_proposed(PROPOSED_REJECTED)
        rejected = ledger.rejected_proposed(proposed)
        active = ledger.active_proposed(proposed)
        allowed = ({v['value'] for v in confirmed.values()}
                   | {v['value'] for v in active.values()})
        errs = checks.scan_code(allowed, [('src/pages/a.tsx', '"#2D7FF9"')], rejected=rejected)
        self.assertEqual(len(errs), 1)
        self.assertIn('info', errs[0])
        self.assertIn('반려', errs[0])
        self.assertNotEqual(errs[0], 'src/pages/a.tsx: 원장에 없는 색 #2D7FF9')

    def test_반려된_토큰이_theme에_남아있으면_반려_사실을_명시한다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        proposed = ledger.parse_proposed(PROPOSED_REJECTED)
        rejected = ledger.rejected_proposed(proposed)
        css = CheckThemeTest.CSS_OK.replace('}', '  --color-info: #2D7FF9;\n}')
        errs = checks.check_theme(confirmed, {}, shape, css, rejected=rejected)
        self.assertTrue(any('info' in e and '반려' in e for e in errs))


TYPO_FM = """---
typography:
  headline:   { fontFamily: 'GT Maru', fontWeight: 900, fontSize: { pc: '1.75rem', mobile: '1.375rem' }, letterSpacing: '-0.06em', lineHeight: '95%', textTransform: uppercase }
  body:       { fontFamily: 'Inter', fontWeight: 400, fontSize: '1rem', letterSpacing: '0', lineHeight: '123%' }
fontFamilies:
  stack-maru: "'GT Maru', var(--font-inter-next), 'Pretendard Variable', sans-serif"
  stack-inter: "var(--font-inter-next), Inter, 'Pretendard Variable', sans-serif"
hangulTracking:
  scope: "html[lang='ko']"
  tokens: 'headline, subhead'
  letterSpacing: '-0.03em'
motion:
  duration-fast: '150ms'
  ease-standard: 'ease-out'
---
"""

# --color-*/--radius-* 리셋 라인과 --fs-* 반응형 변수를 실제 global.css 처럼 섞어 둔다 —
# check_motion 의 역방향 검사가 이들을 오탐하지 않는지 "일치하면 에러가 없다" 테스트가
# 함께 검증한다.
TYPO_CSS_OK = """@theme {
  --color-*: initial;
  --radius-*: initial;
  --font-maru: 'GT Maru', var(--font-inter-next), 'Pretendard Variable', sans-serif;
  --font-inter: var(--font-inter-next), Inter, 'Pretendard Variable', sans-serif;
  --duration-fast: 150ms;
  --ease-standard: ease-out;
}
:root { --fs-headline: 1.75rem; }
@media (max-width: 768px) { :root { --fs-headline: 1.375rem; } }
@layer components {
  .typo-headline {
    font-family: var(--font-maru);
    font-weight: 900;
    font-size: var(--fs-headline);
    line-height: 95%;
    letter-spacing: -0.06em;
    text-transform: uppercase;
  }
  .typo-body {
    font-family: var(--font-inter);
    font-weight: 400;
    font-size: 1rem;
    line-height: 123%;
  }
}
html[lang='ko'] .typo-headline { letter-spacing: -0.03em; }
"""


class ParseTypographyTest(unittest.TestCase):
    def test_고정_크기_토큰을_읽는다(self):
        got = ledger.parse_typography(TYPO_FM)
        self.assertEqual(got['body']['fontFamily'], 'Inter')
        self.assertEqual(got['body']['fontWeight'], '400')
        self.assertEqual(got['body']['fontSize'], '1rem')
        self.assertEqual(got['body']['lineHeight'], '123%')
        self.assertFalse(got['body']['uppercase'])

    def test_반응형_크기_토큰을_읽는다(self):
        got = ledger.parse_typography(TYPO_FM)
        self.assertEqual(got['headline']['fontSizeResponsive'], ('1.75rem', '1.375rem'))
        self.assertIsNone(got['headline']['fontSize'])
        self.assertTrue(got['headline']['uppercase'])
        self.assertEqual(got['headline']['letterSpacing'], '-0.06em')

    def test_서체_스택을_읽는다(self):
        got = ledger.parse_font_stacks(TYPO_FM)
        self.assertEqual(got['maru'], "'GT Maru', var(--font-inter-next), 'Pretendard Variable', sans-serif")
        self.assertEqual(got['inter'], "var(--font-inter-next), Inter, 'Pretendard Variable', sans-serif")

    def test_한글_자간을_읽는다(self):
        got = ledger.parse_hangul_tracking(TYPO_FM)
        self.assertEqual(got['scope'], "html[lang='ko']")
        self.assertEqual(got['letterSpacing'], '-0.03em')
        self.assertEqual(got['tokens'], ['headline', 'subhead'])


class CheckTypographyTest(unittest.TestCase):
    def test_일치하면_에러가_없다(self):
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        self.assertEqual(checks.check_typography(typo, ht, TYPO_CSS_OK), [])

    def test_weight_불일치를_잡는다(self):
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace('font-weight: 900;', 'font-weight: 800;')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('headline' in e and 'weight' in e for e in errs))

    def test_반응형_크기_불일치를_잡는다(self):
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace('--fs-headline: 1.375rem', '--fs-headline: 1.5rem')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('headline' in e and '반응형' in e for e in errs))

    def test_클래스_누락을_잡는다(self):
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace('.typo-body {', '.typo-bodyy {')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('typo-body' in e for e in errs))

    def test_한글_자간_선택자_누락을_잡는다(self):
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace("html[lang='ko'] .typo-headline { letter-spacing: -0.03em; }", '')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('자간' in e for e in errs))

    def test_원장에_없는_typo_클래스를_잡는다(self):
        """global.css 의 .typo-* 가 DESIGN.md typography 에 없으면 잡는다 (역방향)."""
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace(
            '  .typo-body {',
            '  .typo-caption {\n    font-family: var(--font-inter);\n  }\n  .typo-body {')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('typo-caption' in e for e in errs))

    def test_weight_뒤에_다른_숫자가_붙은_경우도_잡는다(self):
        """원장 900 이 CSS 의 9000 문자열 접두사로 우연히 매치되면 안 된다 (Fix Round 1 Finding 1)."""
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace('font-weight: 900;', 'font-weight: 9000;')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('headline' in e and 'weight' in e for e in errs))

    def test_letterSpacing_0_토큰은_선언_없으면_통과한다(self):
        """원장 letterSpacing: '0' 인 body 는 CSS 에 letter-spacing 선언이 없어도 통과한다
        (실제 8토큰 중 6개가 이 형태다) — Fix Round 1 Finding 2."""
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        errs = checks.check_typography(typo, ht, TYPO_CSS_OK)
        self.assertFalse(any('typo-body:' in e and 'letter-spacing' in e for e in errs))

    def test_letterSpacing_0_토큰에_0이_아닌_값이_있으면_잡는다(self):
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace(
            '  .typo-body {\n    font-family: var(--font-inter);',
            '  .typo-body {\n    letter-spacing: -0.04em;\n    font-family: var(--font-inter);')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('typo-body' in e and 'letter-spacing' in e for e in errs))

    def test_letterSpacing_비0_불일치는_여전히_잡는다(self):
        """회귀 확인 — headline(-0.06em) 처럼 letterSpacing 이 0 이 아닌 토큰의 불일치 검출은
        Finding 2 수정 이후에도 그대로 동작한다."""
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace('letter-spacing: -0.06em;', 'letter-spacing: -0.05em;')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('headline' in e and 'letter-spacing' in e for e in errs))

    def test_uppercase가_아닌데_CSS에_있으면_잡는다(self):
        """원장에 textTransform 이 없는 body 에 CSS 가 uppercase 를 덧붙이면 잡는다
        (Fix Round 1 Finding 3 — 기존엔 누락만 보고 과다는 안 봤다)."""
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        css = TYPO_CSS_OK.replace(
            '  .typo-body {\n    font-family: var(--font-inter);',
            '  .typo-body {\n    text-transform: uppercase;\n    font-family: var(--font-inter);')
        errs = checks.check_typography(typo, ht, css)
        self.assertTrue(any('typo-body' in e and 'uppercase' in e for e in errs))

    def test_매핑되지_않은_fontFamily는_보고된다(self):
        """F5 — FONT_VAR 에 없는 3번째 서체는 검사를 조용히 건너뛰지 않고 실패로 잡는다."""
        typo_fm = TYPO_FM.replace("fontFamily: 'Inter'", "fontFamily: 'Roboto'")
        typo = ledger.parse_typography(typo_fm)
        ht = ledger.parse_hangul_tracking(typo_fm)
        errs = checks.check_typography(typo, ht, TYPO_CSS_OK)
        self.assertTrue(any('body' in e and 'Roboto' in e for e in errs))

    def test_두_known_얼굴은_기존처럼_통과한다(self):
        """회귀 확인 — GT Maru/Inter 는 fail-closed 이후에도 '매핑되지 않음'으로 안 잡힌다."""
        typo = ledger.parse_typography(TYPO_FM)
        ht = ledger.parse_hangul_tracking(TYPO_FM)
        errs = checks.check_typography(typo, ht, TYPO_CSS_OK)
        self.assertFalse(any('매핑되지 않은' in e for e in errs))


class CheckFontStacksTest(unittest.TestCase):
    def test_일치하면_에러가_없다(self):
        stacks = ledger.parse_font_stacks(TYPO_FM)
        self.assertEqual(checks.check_font_stacks(stacks, TYPO_CSS_OK), [])

    def test_한글_폴백_누락을_잡는다(self):
        stacks = ledger.parse_font_stacks(TYPO_FM)
        css = TYPO_CSS_OK.replace(
            "--font-maru: 'GT Maru', var(--font-inter-next), 'Pretendard Variable', sans-serif;",
            "--font-maru: 'GT Maru', sans-serif;")
        errs = checks.check_font_stacks(stacks, css)
        self.assertTrue(any('maru' in e for e in errs))


class CheckMotionTest(unittest.TestCase):
    def test_일치하면_에러가_없다(self):
        self.assertEqual(checks.check_motion(ledger.parse_motion(TYPO_FM), TYPO_CSS_OK), [])

    def test_값_불일치를_잡는다(self):
        css = TYPO_CSS_OK.replace('--duration-fast: 150ms;', '--duration-fast: 200ms;')
        errs = checks.check_motion(ledger.parse_motion(TYPO_FM), css)
        self.assertTrue(any('duration-fast' in e for e in errs))

    def test_css_변수_누락을_잡는다(self):
        css = TYPO_CSS_OK.replace('  --ease-standard: ease-out;\n', '')
        errs = checks.check_motion(ledger.parse_motion(TYPO_FM), css)
        self.assertTrue(any('--ease-standard' in e for e in errs))

    def test_원장에_motion이_없으면_잡는다(self):
        self.assertEqual(checks.check_motion({}, TYPO_CSS_OK), ['DESIGN.md motion 블록 누락'])

    def test_원장에_없는_모션_변수를_잡는다(self):
        """global.css 의 --duration-*/--ease-*/--press-*/--hover-* 가 DESIGN.md motion 에
        없으면 잡는다 (역방향). --color-*/--radius-* 리셋과 --fs-* 는 TYPO_CSS_OK 에 이미
        섞여 있으므로 이 테스트를 포함한 이 클래스 전체가 그것들을 오탐하지 않음도 함께
        확인한다."""
        css = TYPO_CSS_OK.replace(
            '  --ease-standard: ease-out;\n',
            '  --ease-standard: ease-out;\n  --duration-slow: 400ms;\n')
        errs = checks.check_motion(ledger.parse_motion(TYPO_FM), css)
        self.assertTrue(any('duration-slow' in e for e in errs))


class CheckNoExternalUrlTest(unittest.TestCase):
    def test_외부_url_없으면_통과한다(self):
        self.assertEqual(checks.check_no_external_url(TYPO_CSS_OK), [])

    def test_외부_url을_잡는다(self):
        css = TYPO_CSS_OK + "\n@import url('https://fonts.googleapis.com/css2?family=Roboto');\n"
        errs = checks.check_no_external_url(css)
        self.assertEqual(len(errs), 1)
        self.assertIn('fonts.googleapis.com', errs[0])

    def test_프로토콜_상대_url도_잡는다(self):
        """스킴 없는 //host 형태도 외부 참조다 (Fix Round 1 Finding 4)."""
        css = TYPO_CSS_OK + "\n@import '//fonts.googleapis.com/css2?family=Roboto';\n"
        errs = checks.check_no_external_url(css)
        self.assertEqual(len(errs), 1)
        self.assertIn('fonts.googleapis.com', errs[0])

    def test_패키지_경로는_통과한다(self):
        """'pretendard/dist/...' 같은 슬래시 없는 bare specifier 는 외부 URL 이 아니다."""
        css = TYPO_CSS_OK + (
            "\n@import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';\n")
        self.assertEqual(checks.check_no_external_url(css), [])

    def test_로컬_폰트_url은_통과한다(self):
        """'/font/...' 처럼 슬래시 1개인 루트 상대 경로는 로컬 자산이다."""
        css = TYPO_CSS_OK + (
            "\n@font-face { src: url('/font/GT-Maru-Regular.woff2') format('woff2'); }\n")
        self.assertEqual(checks.check_no_external_url(css), [])


class EntrypointCanaryTest(unittest.TestCase):
    """check-design-tokens.py 자체를 대상으로 한 유일한 테스트.

    나머지 59+ 개 테스트는 전부 ledger/checks 를 문자열 픽스처로만 검사한다 — SCAN_DIRS 를
    좁히거나 SCAN_SUFFIXES 에서 확장자를 빼는 변경은 초록 스위트를 유지한 채로 게이트를
    무력화한다(F1/F2/F4 가 사는 표면 그대로). 값을 못 박아 그 회귀를 막는다."""

    def test_scan_dirs에_app과_src가_있다(self):
        self.assertIn('app', gate.SCAN_DIRS)
        self.assertIn('src', gate.SCAN_DIRS)

    def test_scan_suffixes에_필요한_확장자가_모두_있다(self):
        for suffix in ('.ts', '.tsx', '.css', '.js', '.jsx'):
            self.assertIn(suffix, gate.SCAN_SUFFIXES)


def _f(src):
    """스캐너 테스트용 단일 파일 시퀀스."""
    return [('src/pages/a.tsx', src)]


class ScanArbitraryValueTest(unittest.TestCase):
    def test_임의_색값을_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="bg-[#3B82F6]" />'))
        self.assertTrue(any('bg-[#3B82F6]' in e for e in errs), errs)

    def test_임의_여백값을_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="p-[13px]" />'))
        self.assertTrue(any('p-[13px]' in e for e in errs), errs)

    def test_임의_글자크기를_잡는다(self):
        errs = checks.scan_utilities(_f('<p className="text-[10px]" />'))
        self.assertTrue(any('text-[10px]' in e for e in errs), errs)

    def test_메시지에_파일과_줄번호가_있다(self):
        errs = checks.scan_utilities([('src/pages/a.tsx', '\n\n<div className="p-[13px]" />')])
        self.assertTrue(any('src/pages/a.tsx:3' in e for e in errs), errs)

    def test_CSS변수_참조_문법은_통과한다(self):
        self.assertEqual(checks.scan_utilities(_f('<div className="duration-(--duration-fast)" />')), [])


class ScanInlineStyleTest(unittest.TestCase):
    def test_인라인_스타일을_잡는다(self):
        errs = checks.scan_utilities(_f('<div style={{ color: "red" }} />'))
        self.assertTrue(any('style=' in e for e in errs), errs)

    def test_style_문자열_속성은_통과한다(self):
        self.assertEqual(checks.scan_utilities(_f('<div className="styled-box" />')), [])


class ScanSpacingTest(unittest.TestCase):
    def test_원장_여백은_통과한다(self):
        src = '<div className="p-1 px-1.5 py-2 m-3 mt-4 gap-6 gap-x-8 space-y-12 mb-16" />'
        self.assertEqual(checks.scan_utilities(_f(src)), [])

    def test_원장에_없는_여백_인덱스를_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="p-5" />'))
        self.assertTrue(any('p-5' in e for e in errs), errs)

    def test_0과_auto와_px는_통과한다(self):
        self.assertEqual(checks.scan_utilities(_f('<div className="p-0 mx-auto border-px" />')), [])

    def test_음수_마진도_인덱스를_본다(self):
        errs = checks.scan_utilities(_f('<div className="-mt-5" />'))
        self.assertTrue(any('mt-5' in e for e in errs), errs)

    def test_여백이_아닌_치수는_보지_않는다(self):
        self.assertEqual(checks.scan_utilities(_f('<div className="w-5 h-7 inset-9" />')), [])


class ScanMotionUtilityTest(unittest.TestCase):
    def test_숫자_duration을_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="duration-200" />'))
        self.assertTrue(any('duration-200' in e for e in errs), errs)

    def test_원장_밖_ease를_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="ease-in-out" />'))
        self.assertTrue(any('ease-in-out' in e for e in errs), errs)

    def test_원장_ease는_통과한다(self):
        self.assertEqual(checks.scan_utilities(_f('<div className="ease-standard" />')), [])


class ScanScopeTest(unittest.TestCase):
    def test_css_파일도_인라인스타일_검사는_건너뛴다(self):
        self.assertEqual(checks.scan_utilities([('src/app/global.css', '.x { color: red }')]), [])

    def test_css_정의부의_모션_값은_통과한다(self):
        """--ease-standard: ease-out; 의 ease-out 은 CSS timing-function 키워드이고
        --duration-fast: 150ms 의 150ms 는 CSS 값이다 — 둘 다 Tailwind 클래스명이 아니다.
        .css 는 정의부이므로 scan_utilities 가 아예 스킵해야 오탐하지 않는다."""
        css = (
            '@theme {\n'
            '  --duration-fast: 150ms;\n'
            '  --ease-standard: ease-out;\n'
            '  --press-offset: 4px 5px;\n'
            '}\n'
        )
        self.assertEqual(checks.scan_utilities([('src/app/global.css', css)]), [])

    def test_ts_파일도_임의값_검사를_받는다(self):
        """코드 파일 게이트가 .tsx/.jsx 로만 좁혀지지 않았는지 확인한다 — .ts 도 스캔 대상."""
        errs = checks.scan_utilities([('src/lib/style.ts', 'const cls = "p-[13px]";')])
        self.assertTrue(any('p-[13px]' in e for e in errs), errs)


class ScanArbitraryPropertyTest(unittest.TestCase):
    """F1 — 대괄호 임의 *속성* 문법(`[padding:13px]`)은 접두사가 없어 ARBITRARY_RE 를
    피해간다. 별도 정규식·별도 메시지로 잡는다."""

    def test_임의_속성_padding을_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="[padding:13px]" />'))
        self.assertTrue(any('[padding:13px]' in e for e in errs), errs)
        self.assertTrue(any('임의 속성' in e for e in errs), errs)

    def test_임의_속성_color_rgb를_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="[color:rgb(59,130,246)]" />'))
        self.assertTrue(any('[color:rgb(59,130,246)]' in e for e in errs), errs)

    def test_배열_인덱스는_통과한다(self):
        self.assertEqual(checks.scan_utilities(_f('const x = arr[0];')), [])

    def test_문자열_키_접근도_통과한다(self):
        self.assertEqual(checks.scan_utilities(_f('const x = obj["key"];')), [])

    def test_TS_제네릭_튜플도_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('const x: Array<[string, number]> = [];')), [])


class ScanVariantBracketExemptionTest(unittest.TestCase):
    """F4 — 표준 Tailwind 변형 선택자(`data-[...]:`, `aria-[...]:` 등)는 임의값이 아니다.
    값이 없는 선택자 문법이므로 임의값 검사에서 빼야 한다."""

    def test_data_state_변형은_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="data-[state=open]:bg-accent" />')), [])

    def test_aria_current_변형은_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="aria-[current=page]:p-4" />')), [])

    def test_supports_변형은_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="supports-[display:grid]:p-4" />')), [])

    def test_max_변형은_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="max-[600px]:p-4" />')), [])

    def test_group_data_변형은_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="group-data-[open]:p-4" />')), [])

    def test_임의값_bg는_여전히_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="bg-[#3B82F6]" />'))
        self.assertTrue(any('bg-[#3B82F6]' in e for e in errs), errs)

    def test_임의값_p는_여전히_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="p-[13px]" />'))
        self.assertTrue(any('p-[13px]' in e for e in errs), errs)

    def test_임의값_text는_여전히_잡는다(self):
        errs = checks.scan_utilities(_f('<p className="text-[10px]" />'))
        self.assertTrue(any('text-[10px]' in e for e in errs), errs)


class EaseParenExemptionTest(unittest.TestCase):
    """F6 — `ease-(--ease-X)` 는 원장 CSS 변수 참조 문법이다. 괄호 예외가 없어 두 번째
    이징 토큰부터 정상 사용이 막힌다."""

    def test_ease_paren_standard는_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="ease-(--ease-standard)" />')), [])

    def test_ease_paren_spring도_통과한다(self):
        self.assertEqual(
            checks.scan_utilities(_f('<div className="ease-(--ease-spring)" />')), [])

    def test_ease_in_out은_여전히_잡는다(self):
        errs = checks.scan_utilities(_f('<div className="ease-in-out" />'))
        self.assertTrue(any('ease-in-out' in e for e in errs), errs)


class RemediationCategoryTest(unittest.TestCase):
    """F5 — 색 전용 교정문구가 모든 위반 유형에 붙어 있었다. 카테고리별로 갈라야 한다."""

    def test_여백_위반_메시지는_색_교정문구가_아니다(self):
        errs = checks.scan_utilities(_f('<div className="p-5" />'))
        self.assertTrue(errs)
        self.assertNotIn('팔레트', errs[0])

    def test_모션_위반_메시지는_색_교정문구가_아니다(self):
        errs = checks.scan_utilities(_f('<div className="duration-200" />'))
        self.assertTrue(errs)
        self.assertNotIn('팔레트', errs[0])

    def test_이징_위반_메시지는_색_교정문구가_아니다(self):
        errs = checks.scan_utilities(_f('<div className="ease-in-out" />'))
        self.assertTrue(errs)
        self.assertNotIn('팔레트', errs[0])

    def test_인라인_스타일_메시지는_색_교정문구가_아니다(self):
        errs = checks.scan_utilities(_f('<div style={{ color: "red" }} />'))
        self.assertTrue(errs)
        self.assertNotIn('팔레트', errs[0])

    def test_임의값_메시지는_색_교정문구가_아니다(self):
        errs = checks.scan_utilities(_f('<div className="p-[13px]" />'))
        self.assertTrue(errs)
        self.assertNotIn('팔레트', errs[0])

    def test_임의_속성_메시지는_색_교정문구가_아니다(self):
        errs = checks.scan_utilities(_f('<div className="[padding:13px]" />'))
        self.assertTrue(errs)
        self.assertNotIn('팔레트', errs[0])

    def test_색_위반_메시지는_기존_색_교정문구를_유지한다(self):
        text = 'const c = "#3B82F6";\n'
        errs = checks.scan_code(set(), [('src/pages/a.tsx', text)])
        self.assertTrue(
            any('팔레트에서 가장 가까운 토큰으로 교체하라' in e for e in errs), errs)


class CheckNoExtraStylesheetsTest(unittest.TestCase):
    """F2 — global.css 외의 두 번째 .css 는 어떤 검사에도 안 걸린다. 존재 자체를 막는다."""

    def test_global_css만_있으면_통과한다(self):
        files = [('src/app/global.css', '@theme {}')]
        self.assertEqual(checks.check_no_extra_stylesheets(files), [])

    def test_두번째_스타일시트를_잡는다(self):
        files = [
            ('src/app/global.css', '@theme {}'),
            ('src/pages/home.module.css',
             '.card{padding:13px;color:rgb(59,130,246);'
             'transition:all 3s linear;background:url(https://evil.example.com/a.png)}'),
        ]
        errs = checks.check_no_extra_stylesheets(files)
        self.assertTrue(any('src/pages/home.module.css' in e for e in errs), errs)
        self.assertTrue(any('global.css' in e for e in errs), errs)

    def test_app_밑_css도_잡는다(self):
        files = [('app/extra.css', '.x{color:red}')]
        errs = checks.check_no_extra_stylesheets(files)
        self.assertTrue(any('app/extra.css' in e for e in errs), errs)

    def test_css가_아닌_파일은_안_잡는다(self):
        files = [('src/pages/a.tsx', 'const x = 1;')]
        self.assertEqual(checks.check_no_extra_stylesheets(files), [])


class CheckVarRefsTest(unittest.TestCase):
    """코드가 참조하는 CSS 변수가 @theme 에 실재하는지."""

    CSS = """@theme {
  --duration-standard: 250ms;
  --hover-lift: -2px;
  --press-offset-x: 4px;
  --press-offset-y: 5px;
  --color-*: initial;
}"""

    def test_선언된_변수_참조는_통과한다(self):
        errs = checks.check_var_refs(
            _f('<div className="duration-(--duration-standard)" />'), self.CSS)
        self.assertEqual(errs, [])

    def test_없는_변수_참조를_잡는다(self):
        errs = checks.check_var_refs(
            _f('<div className="duration-(--duraiton-standard)" />'), self.CSS)
        self.assertTrue(any('--duraiton-standard' in e for e in errs), errs)

    def test_오타에_가까운_이름을_제안한다(self):
        errs = checks.check_var_refs(
            _f('<div className="duration-(--duraiton-standard)" />'), self.CSS)
        self.assertTrue(any('--duration-standard 를 쓰려던 것인가' in e for e in errs), errs)

    def test_축별_변수_참조가_통과한다(self):
        errs = checks.check_var_refs(_f(
            '<div className="translate-x-(--press-offset-x) '
            'translate-y-(--press-offset-y) translate-y-(--hover-lift)" />'), self.CSS)
        self.assertEqual(errs, [])

    def test_메시지에_파일과_줄번호가_있다(self):
        errs = checks.check_var_refs(
            [('src/pages/a.tsx', '\n\n<div className="ease-(--ease-spring)" />')], self.CSS)
        self.assertTrue(any('src/pages/a.tsx:3' in e for e in errs), errs)

    def test_메시지가_교정_지시문을_담는다(self):
        errs = checks.check_var_refs(_f('<div className="ease-(--nope)" />'), self.CSS)
        self.assertTrue(any('global.css 는 편집 금지다' in e for e in errs), errs)

    def test_css_파일은_보지_않는다(self):
        """.css 는 선언부다 — var(--x) 사용을 대조 대상으로 삼지 않는다."""
        errs = checks.check_var_refs(
            [('src/app/global.css', '.x { translate: var(--없는것); }')], self.CSS)
        self.assertEqual(errs, [])

    def test_리셋_라인은_선언으로_치지_않는다(self):
        """--color-*: initial; 의 `*` 는 이름이 아니다 — color-* 참조가 통과하면 안 된다."""
        errs = checks.check_var_refs(_f('<div className="bg-(--color-nope)" />'), self.CSS)
        self.assertTrue(errs, errs)

    def test_원장에_없는_Tailwind_내장변수도_잡는다(self):
        """--spacing 은 Tailwind 가 주지만 원장에 없다. 가리키는 것 자체가 드리프트다."""
        errs = checks.check_var_refs(_f('<div className="p-(--spacing)" />'), self.CSS)
        self.assertTrue(any('--spacing' in e for e in errs), errs)


FAMILIES = {
    'colors': {'accent', 'background-shade', 'text'},
    'rounded': {'small', 'card', 'pill'},
    'borders': {'emphasis', 'hairline'},
    'shadows': {'extruded'},
    'typography': {'label', 'body'},
    'motion': {'hover-lift', 'press-offset-x'},
    'spacing': {'1', '1.5', '2', '3', '4', '6', '8', '12', '16'},
}


def _sc(body):
    """컴포넌트 원장 텍스트 — frontmatter + 본문."""
    return f'---\ncomponents:\n{body}---\n\n# 본문\n'


class CheckComponentRefsTest(unittest.TestCase):
    def test_실재하는_참조는_통과한다(self):
        sc = _sc("  card:\n    surface: '{colors.background-shade}'\n"
                 "    rounded: '{rounded.card}'\n    padding: '{spacing.4}'\n")
        self.assertEqual(checks.check_component_refs(sc, FAMILIES), [])

    def test_리터럴을_잡는다(self):
        errs = checks.check_component_refs(_sc('  card:\n    padding: 16px\n'), FAMILIES)
        self.assertTrue(any('토큰 참조가 아니다' in e for e in errs), errs)

    def test_hex_리터럴을_잡는다(self):
        errs = checks.check_component_refs(_sc("  card:\n    surface: '#24F351'\n"), FAMILIES)
        self.assertTrue(any('토큰 참조가 아니다' in e for e in errs), errs)

    def test_원장에_없는_토큰을_잡는다(self):
        errs = checks.check_component_refs(_sc("  card:\n    padding: '{spacing.5}'\n"), FAMILIES)
        self.assertTrue(any('spacing 에 없다' in e for e in errs), errs)

    def test_가까운_이름을_제안한다(self):
        errs = checks.check_component_refs(_sc("  b:\n    r: '{rounded.smal}'\n"), FAMILIES)
        self.assertTrue(any('{rounded.small} 를 쓰려던 것인가' in e for e in errs), errs)

    def test_없는_계열을_잡는다(self):
        errs = checks.check_component_refs(_sc("  b:\n    z: '{elevation.high}'\n"), FAMILIES)
        self.assertTrue(any('계열 elevation 이 원장에 없다' in e for e in errs), errs)

    def test_none_과_transparent_는_통과한다(self):
        sc = _sc('  card:\n    shadow: none\n    fill: transparent\n')
        self.assertEqual(checks.check_component_refs(sc, FAMILIES), [])

    def test_부모_키는_값으로_보지_않는다(self):
        sc = _sc("  card:\n    surface: '{colors.accent}'\n  card-on-dark:\n"
                 "    surface: '{colors.text}'\n")
        self.assertEqual(checks.check_component_refs(sc, FAMILIES), [])

    def test_줄번호가_맞다(self):
        errs = checks.check_component_refs(_sc('  card:\n    padding: 16px\n'), FAMILIES)
        self.assertTrue(any(':4:' in e for e in errs), errs)

    def test_frontmatter_가_없으면_통과한다(self):
        self.assertEqual(checks.check_component_refs('# 본문만 있다\n', FAMILIES), [])


class UnwiredProposedTest(unittest.TestCase):
    CSS = '@theme {\n  --color-accent: #24F351;\n}'

    def test_배선된_제안은_통지하지_않는다(self):
        self.assertEqual(checks.unwired_proposed({'accent': {}}, self.CSS), [])

    def test_배선_안_된_제안을_통지한다(self):
        self.assertEqual(checks.unwired_proposed({'info': {}}, self.CSS), ['info'])


class CheckUnwiredUsageTest(unittest.TestCase):
    def test_배선_안_된_색을_쓰면_막는다(self):
        errs = checks.check_unwired_usage(_f('<p className="text-info" />'), ['info'])
        self.assertTrue(any('text-info' in e for e in errs), errs)

    def test_bg_와_border_도_잡는다(self):
        errs = checks.check_unwired_usage(_f('<p className="bg-info border-info" />'), ['info'])
        self.assertEqual(len(errs), 2, errs)

    def test_쓰지_않으면_통과한다(self):
        self.assertEqual(checks.check_unwired_usage(_f('<p className="text-text" />'), ['info']), [])

    def test_미배선이_없으면_통과한다(self):
        self.assertEqual(checks.check_unwired_usage(_f('<p className="text-info" />'), []), [])

    def test_이름이_부분일치해도_잡지_않는다(self):
        errs = checks.check_unwired_usage(_f('<p className="text-information" />'), ['info'])
        self.assertEqual(errs, [], errs)


class ThemeMissingSplitTest(unittest.TestCase):
    """제안층 미배선은 에러가 아니고 확정층 미배선은 에러다."""

    CSS = """@theme {
  --color-*: initial;
  --radius-*: initial;
  --color-accent: #24F351;
  --color-danger: #C41E1E;
  --radius-small: 10px;
  --radius-card: 24px;
  --radius-pill: 999px;
  --shadow-extruded: 4px 5px 0 #070707;
}"""

    def test_제안층만_있고_theme에_없어도_통과한다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        proposed = {'info': {'value': '#2D7FF9'}}
        self.assertEqual(checks.check_theme(confirmed, proposed, shape, self.CSS), [])

    def test_확정층이_theme에_없으면_막는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS.replace('  --color-danger: #C41E1E;\n', '')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('danger' in e for e in errs), errs)

    def test_확정층_누락_메시지가_교정_지시문을_담는다(self):
        confirmed = ledger.parse_confirmed(CONFIRMED_FM)
        shape = ledger.parse_shape(CONFIRMED_FM)
        css = self.CSS.replace('  --color-danger: #C41E1E;\n', '')
        errs = checks.check_theme(confirmed, {}, shape, css)
        self.assertTrue(any('사용자에게 요청하라' in e for e in errs), errs)


if __name__ == '__main__':
    unittest.main()
