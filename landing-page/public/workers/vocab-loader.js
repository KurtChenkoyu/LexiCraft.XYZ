/**
 * Vocabulary Loader Web Worker
 * 
 * Responsibilities:
 * - Download vocabulary.json
 * - Parse JSON to array
 * - Return parsed data via postMessage
 * - DO NOT write to IndexedDB (main thread handles that)
 */

const VOCABULARY_VERSION = '6.19-comprehensive-senses'

self.onmessage = async (event) => {
  const { action } = event.data

  if (action === 'check') {
    // Signal main thread to check its own IndexedDB
    self.postMessage({ status: 'check_main_thread' })
  }

  if (action === 'hydrate') {
    try {
      self.postMessage({ status: 'downloading', progress: 0 })

      // Use version query param to bust HTTP cache when vocabulary changes
      const response = await fetch(`/vocabulary-v6-enriched.json?v=${VOCABULARY_VERSION}`)
      
      // GRACEFUL 404 HANDLING: If file is missing, return empty vocabulary
      if (response.status === 404) {
        console.warn('⚠️ Vocabulary file missing (404), loading empty set')
        self.postMessage({ 
          status: 'parsed', 
          senses: [],
          count: 0,
          version: VOCABULARY_VERSION
        })
        return
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // Stream download with progress
      const contentLength = response.headers.get('content-length')
      let receivedLength = 0
      const reader = response.body.getReader()
      const chunks = []
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        chunks.push(value)
        receivedLength += value.length
        
        if (contentLength) {
          const progress = Math.round((receivedLength / contentLength) * 40)
          self.postMessage({ status: 'downloading', progress })
        }
      }
      
      const blob = new Blob(chunks)
      const text = await blob.text()
      
      self.postMessage({ status: 'parsing', progress: 40 })
      
      const data = JSON.parse(text)
      
      self.postMessage({ status: 'parsing', progress: 60 })

      const senses = data.senses
      if (!senses || typeof senses !== 'object') {
        throw new Error('Invalid vocabulary format: missing senses object')
      }

      // Transform to array (main thread will write to IndexedDB)
      const sensesArray = Object.entries(senses).map(([id, sense]) => ({
        id,
        ...sense
      }))

      self.postMessage({ status: 'parsing', progress: 80 })

      // Send parsed data to main thread
      self.postMessage({ 
        status: 'parsed', 
        senses: sensesArray,
        count: sensesArray.length,
        version: VOCABULARY_VERSION
      })
      
    } catch (error) {
      self.postMessage({ 
        status: 'error', 
        error: error.message || 'Unknown error during hydration' 
      })
    }
  }
}

self.postMessage({ status: 'worker_ready' })

