// 첫 화면. 아직 기획 전이라 자리만 잡아 둔다.
//
// 화면을 만드는 절차는 CLAUDE.md 를, 쓸 수 있는 토큰은 DESIGN.md 를 본다.
// 이 파일에 있던 참조 화면은 원장이 브라우저에서 원장 값대로 그려지는지
// 재기 위한 것이었고, 검증이 끝나 docs/ledger-verification.md 로 옮겼다.
export function HomePage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-2 bg-background p-8">
      <p className="typo-label text-text-subtle">PM yarn@4.10.3</p>
      <h1 className="typo-headline text-text">보일러플레이트</h1>
      <p className="typo-body text-text-subtle">화면은 여기서부터 만든다.</p>
    </main>
  );
}
