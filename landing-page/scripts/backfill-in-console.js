/**
 * Backfill Learner Profiles - Browser Console Script
 * 
 * Copy and paste this entire script into your browser console
 * while logged into the app at http://localhost:3000
 */

(async function() {
  try {
    // Import Supabase client (works in Next.js app)
    const { createClient } = await import('/lib/supabase/client')
    const supabase = createClient()
    
    // Get session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()
    
    if (sessionError || !session) {
      console.error('❌ Not logged in. Please log in first.')
      return
    }
    
    console.log('✅ Authenticated as:', session.user.email)
    console.log('📦 Calling backfill endpoint...')
    
    // Call backfill endpoint
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${API_BASE}/api/users/me/learners/backfill`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    
    const result = await response.json()
    
    console.log('✅ Backfill completed!')
    console.log(`   Created ${result.created_count} learner profile(s)`)
    console.log(`   Message: ${result.message}`)
    
    // Refresh the page to see the changes
    console.log('🔄 Refreshing page to see changes...')
    window.location.reload()
    
  } catch (error) {
    console.error('❌ Error:', error.message)
  }
})()

