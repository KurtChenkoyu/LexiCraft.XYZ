import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import '../globals.css'
import { AnalyticsProvider } from '@/components/features/AnalyticsProvider'
import { AuthProvider } from '@/contexts/AuthContext'
import { UserDataProvider } from '@/contexts/UserDataContext'
import Navbar from '@/components/layout/Navbar'

const inter = Inter({ subsets: ['latin'] })

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}

export async function generateMetadata({
  params: { locale }
}: {
  params: { locale: string }
}): Promise<Metadata> {
  const messages = await getMessages()
  const t = messages as any

  return {
    title: locale === 'zh-TW' 
      ? '賺錢學單字 - 孩子學單字就能賺錢'
      : 'LexiCraft.xyz - Kids Earn Money by Learning Vocabulary',
    description: locale === 'zh-TW'
      ? '孩子透過學習單字賺取真實金錢。家長先投資，孩子努力賺回來。'
      : 'Kids earn real money by mastering vocabulary. Parents invest upfront, kids earn it back.',
    keywords: locale === 'zh-TW'
      ? '孩子學習, 單字, 賺錢, 教育, 台灣, 英文學習'
      : 'kids learning, vocabulary, earn money, education, Taiwan, English learning',
  }
}

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode
  params: { locale: string }
}) {
  // Ensure that the incoming `locale` is valid
  if (!routing.locales.includes(locale as any)) {
    notFound()
  }

  // Providing all messages to the client
  // side is the easiest way to get started
  const messages = await getMessages()

  return (
    <html lang={locale}>
      <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
          <AuthProvider>
            <UserDataProvider>
              <AnalyticsProvider>
                <Navbar currentLocale={locale} />
                {children}
              </AnalyticsProvider>
            </UserDataProvider>
          </AuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}

