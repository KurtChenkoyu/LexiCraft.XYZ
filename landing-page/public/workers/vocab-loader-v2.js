/**
 * Vocabulary Loader Web Worker
 * 
 * Downloads and parses vocabulary.json in background thread.
 * Returns parsed data to main thread (main thread handles IndexedDB).
 */

const VOCABULARY_VERSION = '5.0-gemini'

self.onmessage = async (event) => {
  const { action } = event.data

  if (action === 'check') {
    // Signal main thread to check its own IndexedDB
    self.postMessage({ status: 'check_main_thread' })
  }

  if (action === 'hydrate') {
    try {
      self.postMessage({ status: 'downloading', progress: 0 })

      const response = await fetch('/vocabulary.json')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // Stream progress if possible
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

      // Transform to array (but DON'T write to IndexedDB!)
      const sensesArray = Object.entries(senses).map(([id, sense]) => ({
        id,
        ...sense
      }))

      self.postMessage({ status: 'parsing', progress: 80 })

      // Send data to main thread - main thread will write to IndexedDB
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
