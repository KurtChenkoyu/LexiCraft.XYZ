const createNextIntlPlugin = require('next-intl/plugin')

const withNextIntl = createNextIntlPlugin('./i18n/request.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Transpile framer-motion to avoid module resolution issues
  transpilePackages: ['framer-motion'],
  
  // Enable compression (gzip/brotli)
  compress: true,
  
  // Rewrites to bypass i18n for static assets
  async rewrites() {
    return {
      beforeFiles: [
        // Allow /workers/* to be accessed without locale prefix
        {
          source: '/workers/:path*',
          destination: '/workers/:path*',
          locale: false,
        },
        // Allow vocabulary files to be accessed without locale prefix
        {
          source: '/vocabulary-v6-enriched.json',
          destination: '/vocabulary-v6-enriched.json',
          locale: false,
        },
        // Keep old path for backward compatibility during transition
        {
          source: '/vocabulary.json',
          destination: '/vocabulary.json',
          locale: false,
        }
      ]
    }
  },
  
  // Custom headers for vocabulary files
  async headers() {
    return [
      {
        source: '/vocabulary-v6-enriched.json',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          },
          {
            key: 'Content-Type',
            value: 'application/json'
          }
        ]
      },
      // Old filename - keep for any stale references
      {
        source: '/vocabulary.json',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          },
          {
            key: 'Content-Type',
            value: 'application/json'
          }
        ]
      },
      {
        source: '/workers/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000'
          }
        ]
      }
    ]
  }
}

module.exports = withNextIntl(nextConfig)

