'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import SurveyEngine from '@/components/features/survey/SurveyEngine';

export default function SurveyPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuth();

  const locale = pathname.split('/')[1] || 'zh-TW';

  const handleExit = () => {
    router.push(`/${locale}/dashboard`);
  };

  // user is guaranteed by layout
  return (
    <main className="min-h-screen bg-gray-950">
      <SurveyEngine 
        onExit={handleExit}
        userId={user?.id || ''}
      />
    </main>
  );
}

