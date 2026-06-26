import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useOfflineSync } from './useOfflineSync';

vi.mock('@/lib/offline-queue', () => ({
  getPendingCount: vi.fn().mockResolvedValue(2),
  syncPending: vi.fn().mockResolvedValue({ synced: 2, failed: 0 }),
}));

describe('useOfflineSync', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.defineProperty(navigator, 'onLine', { value: true, writable: true, configurable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts online with showBanner false', () => {
    const { result } = renderHook(() => useOfflineSync());
    expect(result.current.isOnline).toBe(true);
    expect(result.current.showBanner).toBe(false);
  });

  it('detects offline event', async () => {
    const { result } = renderHook(() => useOfflineSync());
    act(() => {
      Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });
      window.dispatchEvent(new Event('offline'));
    });
    expect(result.current.isOnline).toBe(false);
  });

  it('shows banner after 10 minutes offline', async () => {
    const { result } = renderHook(() => useOfflineSync());
    act(() => {
      Object.defineProperty(navigator, 'onLine', { value: false, configurable: true });
      window.dispatchEvent(new Event('offline'));
    });
    act(() => {
      vi.advanceTimersByTime(10 * 60 * 1000 + 100);
    });
    expect(result.current.showBanner).toBe(true);
  });
});
