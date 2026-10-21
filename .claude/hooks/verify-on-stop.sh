#!/bin/bash
# 턴 종료 시 주 검증. 파일이 어떤 도구로 쓰였든 최종 상태를 본다.
#
# 재진입 가드: exit 2 를 내면 에이전트가 작업을 이어간다. 에이전트 힘으로 고칠 수 없는
# 실패(예: 잠금 영역인 src/shared/api 의 타입 오류)면 무한 루프가 된다. stdin 의
# stop_hook_active 가 true 면 이미 이 훅 때문에 재개된 턴이므로 차단하지 않고 보고만 한다.
INPUT=$(cat)
ACTIVE=$(printf '%s' "$INPUT" | python3 -c \
  "import json,sys; print(json.load(sys.stdin).get('stop_hook_active', False))" 2>/dev/null || echo False)

if ! cd "${CLAUDE_PROJECT_DIR:-.}"; then
  if [ "$ACTIVE" = "True" ]; then
    echo "훅이 프로젝트 디렉터리로 여전히 이동하지 못한다 (CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-<미설정>}). 스스로 고칠 수 없는 문제일 수 있으니 사용자에게 보고하라." >&2
    exit 0
  fi
  echo "훅이 프로젝트 디렉터리로 이동하지 못했다 (CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-<미설정>})." >&2
  echo "검증이 실행되지 않았다 — 사용자에게 보고하라." >&2
  exit 2
fi
OUT=$(npm run verify 2>&1)
STATUS=$?
[ $STATUS -eq 0 ] && exit 0

LINES=$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')
print_out() {
  printf '%s\n' "$OUT" | head -60 >&2
  if [ "$LINES" -gt 60 ]; then
    echo "... (총 ${LINES}줄 중 60줄만 표시). 전체는 'npm run verify' 로 직접 확인하라." >&2
  fi
}

if [ "$ACTIVE" = "True" ]; then
  echo "검증이 여전히 실패한다. 스스로 고칠 수 없는 문제일 수 있으니 사용자에게 보고하라." >&2
  print_out
  exit 0
fi

echo "턴을 끝내기 전에 검증이 실패했다. 아래를 고치고 다시 확인하라." >&2
print_out
exit 2
