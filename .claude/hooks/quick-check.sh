#!/bin/bash
# 편집 직후 빠른 피드백(보너스 층). 매칭되지 않는 쓰기 경로가 있으므로 이 층에 의존하지
# 않는다 — 실질 보장은 Stop 훅과 git 훅이 진다. tsc 는 여기서 돌리지 않는다(느리다).
cat > /dev/null
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
OUT=$(npm run check:tokens 2>&1)
[ $? -eq 0 ] && exit 0
echo "$OUT" >&2
exit 2
