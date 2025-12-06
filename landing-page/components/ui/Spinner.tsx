import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  color?: 'primary' | 'white' | 'gray'
}

export function Spinner({ size = 'md', className, color = 'primary' }: SpinnerProps) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-t-transparent',
        {
          'h-4 w-4': size === 'sm',
          'h-8 w-8': size === 'md',
          'h-12 w-12': size === 'lg',
          'h-16 w-16 border-4': size === 'xl',
        },
        {
          'border-cyan-600': color === 'primary',
          'border-white': color === 'white',
          'border-gray-400': color === 'gray',
        },
        className
      )}
    />
  )
}

interface LoadingScreenProps {
  message?: string
  className?: string
}

export function LoadingScreen({ message = '載入中...', className }: LoadingScreenProps) {
  return (
    <div className={cn('min-h-screen flex items-center justify-center', className)}>
      <div className="text-center">
        <Spinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  )
}

