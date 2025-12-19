import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

// Root layout - middleware handles locale routing
// Next.js requires <html> and <body> tags in the root layout
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const path = window.location.pathname;
                  const localeMatch = path.match(/^\\/(zh-TW|en)(\\/|$)/);
                  if (localeMatch && localeMatch[1]) {
                    document.documentElement.lang = localeMatch[1];
                  }
                } catch (e) {
                  console.warn('Failed to set lang attribute:', e);
                }
              })();
            `,
          }}
        />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}
