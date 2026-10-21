#!/bin/bash
# --no-verify 로 git 훅(lint·토큰 게이트)을 건너뛰는 것을 막는다.
#
# 왜 permissions 가 아니라 훅인가: Claude Code 의 Bash 권한 규칙은 접두사 매칭이라
# 명령 "중간" 의 플래그를 매칭하지 못한다. `Bash(git commit * --no-verify*)` 는 작동하지
# 않고(실측), `Bash(git commit:*)` 로 넓히면 모든 커밋이 막혀 쓸 수 없다.
#
# PreToolUse 가 맞는 자리인 이유: 판단 근거가 파일 "내용" 이 아니라 명령 "문자열" 이다.
# 내용 기반 검사는 실행 후에만 가능하지만(그래서 Stop 훅이 주 검증이다), 명령 문자열은
# 실행 전에 볼 수 있으므로 여기서는 실제로 차단이 된다.
#
# F3 — 예전 정규식은 리터럴 `--no-verify` 하나만 봐서 네 가지로 다 새 나갔다: `-n`(짧은
# 플래그), `HUSKY=0`(husky 자체가 모든 훅을 건너뛴다), `core.hooksPath=/dev/null`(훅
# 자체를 무력화), `env git ...`(앵커가 `git` 바로 앞만 허용). 아래는 python3 로 판단을
# 옮겨 네 가지를 전부 막는다 — git 을 호출하는 세그먼트를 찾아(변수 대입·`env`·절대경로
# 접두사를 허용) 그 나머지에서 `--no-verify`·`n` 이 포함된 짧은-대시 플래그 뭉치·
# `core.hooksPath` 를 찾고, `HUSKY=0` 대입은 git 세그먼트 여부와 무관하게 그 자체로 막는다.
# 오탐은 감수한다 — 여기서는 과차단이 안전한 방향이다. echo/grep 처럼 git 을 호출하지
# 않는 세그먼트 안의 문자열 언급은 그대로 통과시킨다(이 훅을 테스트하거나 CLAUDE.md 의
# 해당 줄을 고치는 것까지 막으면 안 된다).
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | python3 -c \
  "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo '')

# 아래 python3 는 heredoc 으로 스크립트 소스 자체를 stdin 으로 읽으므로($CMD 를 여기서
# 파이프로 또 넘기면 stdin 이 script-source 용도와 충돌해 깨진다), CMD 는 환경변수로
# 넘긴다.
CMD="$CMD" python3 - <<'PYEOF'
import os
import re
import sys

cmd = os.environ.get('CMD', '')


def block(reason):
    sys.stderr.write(
        f"--no-verify 는 금지다 (걸린 사유: {reason}). "
        "git 훅(lint·토큰 게이트)을 건너뛰는 경로다.\n")
    sys.stderr.write("게이트에 막혔으면 우회하지 말고 코드를 고쳐라.\n")
    sys.stderr.write("고칠 수 없는 이유가 있으면 사용자에게 말하고 판단을 넘겨라.\n")
    sys.exit(2)


# git 을 실제로 호출하는 세그먼트: 세그먼트 시작(문자열 시작 또는 ; & | 개행 뒤) 다음에
# 변수 대입(`VAR=val `)이 0개 이상, 그다음 `env`(선택), 그다음 절대/상대 경로 접두사(선택),
# 그다음 `git` 이 오는 경우. 나머지(rest)에서 네 가지 우회를 찾는다. rest 는 다음 구분자나
# 줄바꿈 전까지만(개행도 별도 명령의 경계다 — 아니면 뒤 줄의 아무 인자나 앞 git 호출의
# rest 로 잘못 딸려 들어간다. G1 — 이 줄바꿈 경계가 없어서 이 저장소 자신의 브랜치명
# feat/planner-harness-2 를 인자로 쓰는 git 호출까지 막혔었다: "-harness" 의 n 을 짧은
# 플래그로 오인했다).
GIT_INVOKE_RE = re.compile(
    r'(?:^|[;&|\n])\s*'
    r'(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*'
    r'(?:env\s+)?'
    r'(?:[\w./-]*/)?git\b(?P<rest>[^;&|\n]*)'
)

for m in GIT_INVOKE_RE.finditer(cmd):
    rest = m.group('rest')
    # G2 — HUSKY=0 은 예전엔 git 세그먼트와 무관하게 명령 전체에서 찾았다. 그러면
    # `grep HUSKY=0 file` 같은 무관한 읽기 전용 명령까지 막힌다(--no-verify 를 문서화·
    # 테스트하는 것까지 막던 예전 버그와 같은 종류). git 을 실제로 호출하는 세그먼트의
    # rest 안에 있을 때만 본다 — HUSKY=0 은 그 자체로 명령이 아니라 뒤에 오는 명령의
    # 환경을 바꾸는 대입이므로, git 세그먼트 시작부(변수 대입 자리)에 있어야 실제
    # 우회다.
    if re.search(r'(?<![\w-])HUSKY=0\b', m.group(0)):
        block('HUSKY=0')
    if re.search(r'--no-verify\b', rest):
        block('--no-verify')
    # 단일 대시 플래그 뭉치에 n 이 섞여 있으면(-n, -an, -na 등) 막는다. 앞이 공백/시작이어야
    # 한다(?<!\S) — 아니면 core.hooksPath 나 x-shop-front·planner-harness 같은 경로·
    # 브랜치명 안의 "-front"·"-harness" 까지 플래그로 오인한다(G1). `--xxx` 긴 옵션은
    # 두 번째 대시가 공백이 아닌 문자 뒤라 역시 여기 안 걸린다.
    if re.search(r'(?<!\S)-[a-zA-Z]*n[a-zA-Z]*\b', rest):
        block('짧은 플래그 -n')
    if 'core.hooksPath' in rest:
        block('core.hooksPath')

sys.exit(0)
PYEOF
exit $?
