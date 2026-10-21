#!/usr/bin/env node
// Python 3 인터프리터를 찾아 파이썬 스크립트를 실행한다.
//
// 왜 있나 — npm 스크립트에 `python3` 를 하드코딩하면 Windows 에서 깨진다. python.org·
// winget 판 Python 은 `python.exe` 와 `py` 런처만 만들고 `python3` 는 만들지 않는다
// (Microsoft Store 판만 만든다). 그러면 pre-commit 훅이 부르는 check:tokens 가
// "python3: command not found" 로 실패해 **모든 커밋이 막히고**, 기획자는 디자인과
// 아무 상관없는 메시지를 보게 된다.
//
// 사용: node scripts/run-python.mjs [--cwd <디렉터리>] <스크립트.py> [인자...]

import { spawnSync } from 'node:child_process';

// 순서가 의도적이다. python3 를 먼저 보는 이유는 python 이 (드물게) Python 2 인 환경이
// 남아 있기 때문이고, py 를 마지막에 두는 이유는 Windows 전용이기 때문이다.
const CANDIDATES = [
  { cmd: 'python3', pre: [] },
  { cmd: 'python', pre: [] },
  { cmd: 'py', pre: ['-3'] },
];

// 존재만으로는 부족하다 — Microsoft Store 의 python3 스텁은 실행하면 스토어를 열고
// 실패한다. 실제로 3.x 를 뱉는지 확인한다.
function isPython3(cand) {
  const probe = spawnSync(
    cand.cmd,
    [...cand.pre, '-c', 'import sys; print(sys.version_info[0])'],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], shell: false },
  );
  return probe.status === 0 && probe.stdout.trim() === '3';
}

const argv = process.argv.slice(2);
let cwd;
if (argv[0] === '--cwd') {
  cwd = argv[1];
  argv.splice(0, 2);
}

if (argv.length === 0) {
  console.error('run-python.mjs: 실행할 파이썬 스크립트를 인자로 넘겨야 한다.');
  process.exit(2);
}

const found = CANDIDATES.find(isPython3);

if (!found) {
  console.error(
    'Python 3 을 찾지 못했다. 이 레포의 디자인 토큰 게이트가 파이썬 스크립트라\n' +
      '설치돼 있어야 커밋할 수 있다.\n' +
      '\n' +
      '  macOS   : xcode-select --install\n' +
      '  Windows : winget install Python.Python.3.12\n' +
      '            (설치 중 "Add python.exe to PATH" 를 반드시 체크한다)\n' +
      '\n' +
      '설치한 뒤 새 터미널에서 python3 --version 또는 python --version 이\n' +
      '3.x 를 뱉는지 확인한다. 자세한 안내는 README.md 의 "먼저 설치할 것" 에 있다.',
  );
  process.exit(1);
}

const run = spawnSync(found.cmd, [...found.pre, ...argv], {
  stdio: 'inherit',
  cwd,
  shell: false,
});

// 시그널로 죽은 경우 status 는 null 이다 — 그때도 실패로 넘긴다.
process.exit(run.status === null ? 1 : run.status);
