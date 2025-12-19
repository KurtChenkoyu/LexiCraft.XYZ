/**
 * Browser-Compatible Backend Connection Test
 * 
 * Copy and paste this into your browser console to test the connection.
 * This version works in the browser (no Node.js process object needed).
 */

(async function testBackendConnection() {
  console.log('🔍 Testing Backend Connection...\n')
  
  // Get API base URL from window or default
  const API_BASE = window.location.origin.includes('localhost') 
    ? 'http://localhost:8000'
    : (window.__NEXT_DATA__?.env?.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  
  console.log('API Base URL:', API_BASE)
  console.log('Current page origin:', window.location.origin)
  console.log('')
  
  // Test 1: Health check (no auth required)
  console.log('Test 1: Health Check (no auth)')
  try {
    const startTime = Date.now()
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    const elapsed = Date.now() - startTime
    
    if (response.ok) {
      const data = await response.json()
      console.log(`✅ Health check passed (${elapsed}ms)`)
      console.log('   Response:', data)
    } else {
      console.error(`❌ Health check failed: ${response.status} ${response.statusText}`)
    }
  } catch (error) {
    console.error('❌ Health check error:', error.message)
    console.error('   Error type:', error.name)
    console.error('   This usually means:')
    console.error('   1. Backend is not running on port 8000')
    console.error('   2. CORS is blocking the request')
    console.error('   3. Network/firewall issue')
  }
  
  console.log('')
  
  // Test 2: Check CORS
  console.log('Test 2: CORS Check')
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'OPTIONS',
      headers: {
        'Origin': window.location.origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    })
    console.log('   OPTIONS response status:', response.status)
    console.log('   CORS headers:', {
      'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
      'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
    })
  } catch (error) {
    console.warn('   OPTIONS request failed (may be normal):', error.message)
  }
  
  console.log('')
  
  // Test 3: Authenticated endpoint (will fail without token, but tests connection)
  console.log('Test 3: Authenticated Endpoint (expects 401)')
  try {
    const startTime = Date.now()
    const response = await fetch(`${API_BASE}/api/users/me`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    const elapsed = Date.now() - startTime
    const data = await response.json()
    
    if (response.status === 401) {
      console.log(`✅ Connection works (${elapsed}ms) - Got expected 401 (no auth token)`)
      console.log('   Response:', data)
    } else if (response.status === 200) {
      console.log(`✅ Connection works (${elapsed}ms) - Authenticated successfully!`)
    } else {
      console.warn(`⚠️ Unexpected status: ${response.status}`)
      console.log('   Response:', data)
    }
  } catch (error) {
    console.error('❌ Authenticated endpoint error:', error.message)
    if (error.message.includes('timeout')) {
      console.error('   ⚠️ REQUEST TIMED OUT - Backend may be slow or hanging')
    }
  }
  
  console.log('')
  console.log('=== Summary ===')
  console.log('If all tests pass, the backend connection is working.')
  console.log('If you see timeouts, check backend logs for slow queries.')
  console.log('If you see CORS errors, check backend CORS configuration.')
})()


