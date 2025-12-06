'use client'

import React, { useState } from 'react'

interface PreSurveyCalibrationProps {
  onComplete: (cefrLevel: string | undefined, age?: number) => void
}

const CEFR_LEVELS = [
  { value: 'A1', label: 'A1 (Beginner)', description: 'Basic user' },
  { value: 'A2', label: 'A2 (Elementary)', description: 'Basic user' },
  { value: 'B1', label: 'B1 (Intermediate)', description: 'Independent user' },
  { value: 'B2', label: 'B2 (Upper Intermediate)', description: 'Independent user' },
  { value: 'C1', label: 'C1 (Advanced)', description: 'Proficient user' },
  { value: 'C2', label: 'C2 (Mastery)', description: 'Proficient user' },
  { value: 'SKIP', label: 'Skip / Use Default', description: 'Start at market median' },
]

const PreSurveyCalibration: React.FC<PreSurveyCalibrationProps> = ({ onComplete }) => {
  const [cefrLevel, setCefrLevel] = useState<string>('')
  const [age, setAge] = useState<string>('')
  const [errors, setErrors] = useState<{ cefr?: string; age?: string }>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate CEFR level
    if (!cefrLevel) {
      setErrors({ cefr: 'Please select a proficiency level or choose to skip' })
      return
    }

    // Validate age if provided
    if (age) {
      const ageNum = parseInt(age)
      if (isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
        setErrors({ age: 'Please enter a valid age (1-120)' })
        return
      }
    }

    setErrors({})
    
    // Convert SKIP to undefined for default behavior (backend will use market median)
    const finalCefr = cefrLevel === 'SKIP' ? undefined : cefrLevel
    const finalAge = age ? parseInt(age) : undefined
    
    onComplete(finalCefr, finalAge)
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-2xl">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Pre-Survey Calibration
            </h1>
            <p className="text-gray-400 text-lg">
              Help us calibrate your vocabulary assessment
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* CEFR Level Selection */}
            <div>
              <label htmlFor="cefr" className="block text-sm font-semibold text-gray-300 mb-3">
                English Proficiency Level <span className="text-red-400">*</span>
              </label>
              <div className="grid grid-cols-1 gap-3">
                {CEFR_LEVELS.map((level) => (
                  <label
                    key={level.value}
                    className={`
                      flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all
                      ${cefrLevel === level.value
                        ? 'border-cyan-500 bg-cyan-500/10'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="cefr"
                      value={level.value}
                      checked={cefrLevel === level.value}
                      onChange={(e) => {
                        setCefrLevel(e.target.value)
                        setErrors({ ...errors, cefr: undefined })
                      }}
                      className="mr-4 w-4 h-4 text-cyan-500 focus:ring-cyan-500 focus:ring-2"
                    />
                    <div className="flex-1">
                      <div className="text-white font-medium">{level.label}</div>
                      <div className="text-gray-400 text-sm">{level.description}</div>
                    </div>
                  </label>
                ))}
              </div>
              {errors.cefr && (
                <p className="mt-2 text-sm text-red-400">{errors.cefr}</p>
              )}
            </div>

            {/* Age Input (Optional) */}
            <div>
              <label htmlFor="age" className="block text-sm font-semibold text-gray-300 mb-2">
                Age <span className="text-gray-500 text-xs">(Optional)</span>
              </label>
              <input
                type="number"
                id="age"
                value={age}
                onChange={(e) => {
                  setAge(e.target.value)
                  setErrors({ ...errors, age: undefined })
                }}
                min="1"
                max="120"
                placeholder="Enter your age"
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none"
              />
              {errors.age && (
                <p className="mt-2 text-sm text-red-400">{errors.age}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors text-lg"
            >
              Start Survey
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default PreSurveyCalibration

