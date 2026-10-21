import { Inter } from 'next/font/google';
import '@app/global.css';
import { Providers } from '@app/providers';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter-next' });

export const metadata = {
  title: 'PM yarn',
  description: 'PM yarn',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={inter.variable}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
