'use client'

import { useEffect, useState } from 'react'

export default function WordCloud() {
    // Fallback word pool if API fails
    const fallbackWords = [
        'vocabulary', 'learn', 'master', 'fluency', 'comprehension', 'words',
        'reading', 'practice', 'knowledge', 'study', 'language', 'skill',
        'education', 'grammar', 'writing', 'speaking', 'listening', 'memory',
        'achievement', 'progress', 'excellence', 'success', 'growth', 'improvement',
        'proficiency', 'literacy', 'articulate', 'eloquent', 'expression', 'communication',
        'understanding', 'wisdom', 'insight', 'learning', 'retention', 'recall',
        'pronunciation', 'accent', 'dialect', 'semantics', 'syntax', 'lexicon',
        'etymology', 'morphology', 'phonetics', 'linguistics', 'bilingual', 'multilingual',
        'fluent', 'native', 'advanced', 'intermediate', 'beginner', 'expert',
    ]

    const [wordPool, setWordPool] = useState(fallbackWords)
    const [displayWords, setDisplayWords] = useState<any[]>([])
    const [mounted, setMounted] = useState(false)

    // Fetch word list from API on mount
    useEffect(() => {
        // TODO: Replace with your actual API endpoint
        // For now, we'll use the fallback words
        // Example API call:
        // fetch('/api/vocabulary/trending')
        //   .then(res => res.json())
        //   .then(data => setWordPool(data.words))
        //   .catch(() => setWordPool(fallbackWords))

        setWordPool(fallbackWords)
    }, [])

    // Initialize words only on client-side to avoid hydration mismatch
    useEffect(() => {
        if (wordPool.length === 0) return

        const shuffled = [...wordPool].sort(() => Math.random() - 0.5)
        const initialWords = shuffled.slice(0, 30).map((text, i) => ({
            text,
            size: ['text-base', 'text-lg', 'text-xl', 'text-2xl'][Math.floor(Math.random() * 4)],
            duration: 18 + Math.random() * 8,
            delay: Math.random() * 5,
            left: Math.random() * 100,
            top: Math.random() * 40,
            opacity: 1, // Start fully visible
        }))
        setDisplayWords(initialWords)
        setMounted(true)
    }, [wordPool])

    // Smoothly swap words every 15 seconds with fade effect
    useEffect(() => {
        if (!mounted || wordPool.length === 0) return

        const interval = setInterval(() => {
            setDisplayWords(prev => {
                const newWords = [...prev]
                // Swap 2 random words (reduced from 3 for less disruption)
                for (let i = 0; i < 2; i++) {
                    const randomIndex = Math.floor(Math.random() * newWords.length)
                    const randomWord = wordPool[Math.floor(Math.random() * wordPool.length)]

                    // Fade out
                    newWords[randomIndex] = {
                        ...newWords[randomIndex],
                        opacity: 0,
                    }

                    // After fade out, swap the word and fade in
                    setTimeout(() => {
                        setDisplayWords(current => {
                            const updated = [...current]
                            updated[randomIndex] = {
                                ...updated[randomIndex],
                                text: randomWord,
                                left: Math.random() * 100,
                                top: Math.random() * 40,
                                opacity: 1,
                            }
                            return updated
                        })
                    }, 1000) // Wait for fade out to complete
                }
                return newWords
            })
        }, 15000) // Every 15 seconds (increased from 10)

        return () => clearInterval(interval)
    }, [mounted, wordPool])

    // Don't render anything until mounted (client-side only)
    if (!mounted) return null

    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
            {displayWords.map((word, i) => {
                const blur = 0.5 + Math.random() * 1

                return (
                    <div
                        key={`${word.text}-${i}`}
                        className={`absolute ${word.size} font-bold text-white animate-float-wave transition-all duration-1000`}
                        style={{
                            left: `${word.left}%`,
                            top: `${word.top}%`,
                            opacity: (0.2 + Math.random() * 0.15) * word.opacity, // Multiply by word.opacity for fade effect
                            animationDuration: `${word.duration}s`,
                            animationDelay: `${word.delay}s`,
                            filter: `blur(${blur}px)`,
                        }}
                    >
                        {word.text}
                    </div>
                )
            })}
        </div>
    )
}
