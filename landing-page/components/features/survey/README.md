# LexiSurvey Frontend Components

Complete React frontend implementation for the LexiSurvey vocabulary assessment system.

## Components

### SurveyEngine
Main controller component that manages the entire survey flow:
- Initializes survey session via `/api/v1/survey/start`
- Handles answer submissions via `/api/v1/survey/next`
- Manages state transitions (Loading → Question → Complete/Error)
- Displays appropriate UI based on current state

### MultiSelectMatrix
6-option grid input component:
- 2x3 grid layout for options
- Multi-select functionality
- Visual feedback for selected options
- Commit button (active only after selection)

### SurveyProgress
Progress visualization component:
- Shows current phase (Sector Survey / Triangulation / Verification)
- Progress bar with geodetic survey metaphor
- Phase labels aligned with domain language
- Sequential question counter (SEQ: XX / 15)

### ResultDashboard
Final results display:
- Tri-Metric Report visualization (Volume, Reach, Density)
- Summary section
- Action buttons (Restart, Print)

## Usage

```tsx
import { SurveyEngine } from '@/components/survey'

export default function SurveyPage() {
  return (
    <div>
      <SurveyEngine 
        cefrLevel="B1"
        userId="optional_user_id"
        onComplete={(metrics) => {
          console.log('Survey completed:', metrics)
        }}
      />
    </div>
  )
}
```

## API Configuration

The components expect the backend API to be available at:
- Default: `http://127.0.0.1:8000`
- Override with: `NEXT_PUBLIC_API_URL` environment variable

## State Machine

```
Loading → Question → (Answer) → Loading → Question → ... → Complete
   ↓                                                          ↓
 Error ←─────────────────────────────────────────────────── Error
```

## Props

### SurveyEngine
- `cefrLevel?: string` - CEFR level for calibration (A1, A2, B1, B2, C1, C2)
- `userId?: string` - Optional user identifier
- `onComplete?: (metrics) => void` - Callback when survey completes

## Styling

Components use Tailwind CSS and match the existing landing page design system:
- Primary colors from `tailwind.config.js`
- Responsive grid layouts
- Smooth transitions and animations
- Shimmer effect on progress bar

