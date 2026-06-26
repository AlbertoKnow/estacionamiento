'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { getPendingCount, syncPending } from '@/lib/offline-queue';

export interface OfflineSyncState {
  isOnline: boolean;
  pendingCount: number;
  showBanner: boolean;
  syncNow: () => Promise<void>;
}

const BANNER_DELAY_MS = 10 * 60 * 1000; // 10 minutes

export function useOfflineSync(): OfflineSyncState {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [pendingCount, setPendingCount] = useState(0);
  const [showBanner, setShowBanner] = useState(false);
  const bannerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refreshCount = useCallback(async () => {
    const count = await getPendingCount();
    setPendingCount(count);
  }, []);

  const syncNow = useCallback(async () => {
    await syncPending();
    await refreshCount();
    const remaining = await getPendingCount();
    if (remaining === 0) setShowBanner(false);
  }, [refreshCount]);

  useEffect(() => {
    const handleOnline = async () => {
      setIsOnline(true);
      setShowBanner(false);
      if (bannerTimerRef.current) clearTimeout(bannerTimerRef.current);
      await syncNow();
    };

    const handleOffline = () => {
      setIsOnline(false);
      bannerTimerRef.current = setTimeout(() => setShowBanner(true), BANNER_DELAY_MS);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    refreshCount();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (bannerTimerRef.current) clearTimeout(bannerTimerRef.current);
    };
  }, [syncNow, refreshCount]);

  return { isOnline, pendingCount, showBanner, syncNow };
}
