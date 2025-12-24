/**
 * Marketing Layout
 * 
 * This layout applies to all marketing pages (landing pages, promo pages).
 * It overrides the global "Game Viewport" CSS rules to allow scrolling.
 */

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      {/* Override Game Viewport CSS for marketing pages */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
            html, body {
              height: auto !important;
              overflow: auto !important;
              overflow-x: hidden !important;
              position: static !important;
              scrollbar-gutter: stable !important;
            }
          `,
        }}
      />
      {children}
    </>
  )
}

