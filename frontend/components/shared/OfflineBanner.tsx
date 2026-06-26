'use client';

import { WifiOff } from 'lucide-react';
import { useOfflineSync } from '@/hooks/useOfflineSync';

export default function OfflineBanner() {
  const { showBanner, pendingCount, syncNow, isOnline } = useOfflineSync();

  if (!showBanner) return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center gap-3 text-sm text-amber-800">
      <WifiOff size={16} className="text-amber-600 flex-shrink-0" />
      <span className="flex-1">
        Sin conexión hace más de 10 min
        {pendingCount > 0 && ` · ${pendingCount} registro${pendingCount > 1 ? 's' : ''} pendiente${pendingCount > 1 ? 's' : ''}`}
      </span>
      {isOnline && (
        <button
          onClick={syncNow}
          className="text-xs font-medium text-amber-700 underline underline-offset-2"
        >
          Sincronizar ahora
        </button>
      )}
    </div>
  );
}
