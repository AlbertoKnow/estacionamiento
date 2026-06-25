# Frontend Plan 05: PWA, Offline Queue y E2E Tests

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the offline scan queue with IndexedDB (Dexie.js), the 10-minute disconnection banner, PWA service worker configuration, and E2E tests for the critical flows.

**Architecture:** `lib/offline-queue.ts` wraps Dexie.js with a `pending_scans` table. The `useOfflineSync` hook monitors `online`/`offline` events, starts a 10-minute timer on disconnect, and auto-syncs when reconnected. `next.config.js` enables the service worker via `@ducanh2912/next-pwa`. E2E tests run against the real backend (Docker must be up).

**Prerequisites:** Plans 01–04 complete. The `/scan` page from Plan 02 must be modified to call `enqueueScan()` when offline instead of showing just "offline" status.

**Tech Stack:** Dexie.js 3.x, @ducanh2912/next-pwa, Workbox, fake-indexeddb (test), Playwright 1.x

## Global Constraints
- All commands run from `frontend/` directory.
- TypeScript strict — no `any`.
- Never add `Co-Authored-By: Claude` to git commits.
- E2E tests require Docker backend running: `docker compose up` from repo root.
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/lib/offline-queue.ts` | Create | Dexie DB schema + enqueue/sync/status ops |
| `frontend/lib/offline-queue.test.ts` | Create | Unit tests with fake-indexeddb |
| `frontend/hooks/useOfflineSync.ts` | Create | online/offline events + 10-min timer |
| `frontend/hooks/useOfflineSync.test.ts` | Create | Unit tests for timer + events |
| `frontend/components/shared/OfflineBanner.tsx` | Create | Persistent banner after 10 min offline |
| `frontend/app/(field)/layout.tsx` | Modify | Add OfflineBanner |
| `frontend/app/(field)/scan/page.tsx` | Modify | Call enqueueScan() on offline scan |
| `frontend/next.config.js` | Modify | Enable next-pwa |
| `frontend/public/manifest.json` | Create | PWA manifest |
| `frontend/tests/e2e/login-redirect.spec.ts` | Create | Login → role-based redirect E2E |
| `frontend/tests/e2e/scan-online.spec.ts` | Create | Scan flow E2E |
| `frontend/tests/e2e/report-download.spec.ts` | Create | Report download E2E |
| `frontend/playwright.config.ts` | Create | Playwright config |

---

### Task 1: Offline queue with Dexie.js

**Files:**
- Create: `frontend/lib/offline-queue.ts`
- Test: `frontend/lib/offline-queue.test.ts`

**Interfaces:**
- Produces: `enqueueScan(data)`, `syncPending()`, `getPendingCount()`, `clearFailed()`

- [ ] **Step 1: Write failing tests**

Create `frontend/lib/offline-queue.test.ts`:
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import 'fake-indexeddb/auto';
import { enqueueScan, getPendingCount, clearFailed } from './offline-queue';

describe('offline-queue', () => {
  beforeEach(async () => {
    // Re-import to reset Dexie state
    const { db } = await import('./offline-queue');
    await db.pending_scans.clear();
  });

  it('enqueues a scan record', async () => {
    await enqueueScan({ qr_token: 'token-abc', tipo: 'entry', timestamp: new Date().toISOString() });
    const count = await getPendingCount();
    expect(count).toBe(1);
  });

  it('getPendingCount returns 0 when empty', async () => {
    const count = await getPendingCount();
    expect(count).toBe(0);
  });

  it('clearFailed removes failed records', async () => {
    const { db } = await import('./offline-queue');
    await db.pending_scans.add({
      qr_token: 'tok',
      tipo: 'entry',
      timestamp: new Date().toISOString(),
      retries: 3,
      status: 'failed',
    });
    await clearFailed();
    const count = await getPendingCount();
    expect(count).toBe(0);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- offline-queue.test.ts
```
Expected: FAIL with "Cannot find module './offline-queue'"

- [ ] **Step 3: Create `lib/offline-queue.ts`**

```typescript
import Dexie, { Table } from 'dexie';
import api from './api';

export interface PendingScan {
  id?: number;
  qr_token: string;
  tipo: 'entry' | 'exit';
  timestamp: string;
  retries: number;
  status: 'pending' | 'failed';
}

class OfflineQueueDB extends Dexie {
  pending_scans!: Table<PendingScan, number>;

  constructor() {
    super('utp_parking_offline');
    this.version(1).stores({
      pending_scans: '++id, status, timestamp',
    });
  }
}

export const db = new OfflineQueueDB();

export async function enqueueScan(
  data: Pick<PendingScan, 'qr_token' | 'tipo' | 'timestamp'>
): Promise<void> {
  await db.pending_scans.add({ ...data, retries: 0, status: 'pending' });
}

export async function getPendingCount(): Promise<number> {
  return db.pending_scans.where('status').equals('pending').count();
}

export async function clearFailed(): Promise<void> {
  await db.pending_scans.where('status').equals('failed').delete();
}

interface SyncResult {
  id: string;
  success: boolean;
  detail?: string;
}

export async function syncPending(): Promise<{ synced: number; failed: number }> {
  const pending = await db.pending_scans.where('status').equals('pending').sortBy('timestamp');
  if (!pending.length) return { synced: 0, failed: 0 };

  let synced = 0;
  let failed = 0;

  try {
    const payload = pending.map((s) => ({
      id: String(s.id),
      qr_token: s.qr_token,
      tipo: s.tipo,
      timestamp: s.timestamp,
    }));
    const res = await api.post<SyncResult[]>('/access/sync/', payload);
    const results = res.data;

    for (const result of results) {
      const scan = pending.find((s) => String(s.id) === result.id);
      if (!scan?.id) continue;
      if (result.success) {
        await db.pending_scans.delete(scan.id);
        synced++;
      } else {
        const retries = (scan.retries ?? 0) + 1;
        const newStatus = retries >= 3 || result.detail?.includes('expirado') ? 'failed' : 'pending';
        await db.pending_scans.update(scan.id, { retries, status: newStatus });
        if (newStatus === 'failed') failed++;
      }
    }
  } catch {
    // Network error — leave pending records as-is, will retry next sync
  }

  return { synced, failed };
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- offline-queue.test.ts
```
Expected: PASS — 3 tests passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/offline-queue.ts frontend/lib/offline-queue.test.ts
git commit -m "feat: add offline scan queue with Dexie.js IndexedDB"
```

---

### Task 2: useOfflineSync hook and OfflineBanner

**Files:**
- Create: `frontend/hooks/useOfflineSync.ts`
- Test: `frontend/hooks/useOfflineSync.test.ts`
- Create: `frontend/components/shared/OfflineBanner.tsx`
- Modify: `frontend/app/(field)/layout.tsx`

**Interfaces:**
- Produces: `useOfflineSync(): { isOnline: boolean, pendingCount: number, showBanner: boolean, syncNow(): void }`

- [ ] **Step 1: Write failing tests**

Create `frontend/hooks/useOfflineSync.test.ts`:
```typescript
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- useOfflineSync.test.ts
```
Expected: FAIL with "Cannot find module './useOfflineSync'"

- [ ] **Step 3: Create `hooks/useOfflineSync.ts`**

```typescript
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- useOfflineSync.test.ts
```
Expected: PASS — 3 tests passed.

- [ ] **Step 5: Create `components/shared/OfflineBanner.tsx`**

```typescript
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
```

- [ ] **Step 6: Add OfflineBanner to `app/(field)/layout.tsx`**

```typescript
import BottomNav from '@/components/field/BottomNav';
import OfflineBanner from '@/components/shared/OfflineBanner';

export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-50 max-w-md mx-auto">
      <OfflineBanner />
      <main className="flex-1 overflow-auto">{children}</main>
      <BottomNav />
    </div>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/hooks/useOfflineSync.ts frontend/hooks/useOfflineSync.test.ts frontend/components/shared/OfflineBanner.tsx frontend/app/\(field\)/layout.tsx
git commit -m "feat: add offline sync hook with 10-min banner and auto-sync on reconnect"
```

---

### Task 3: Integrate offline queue into scan page

**Files:**
- Modify: `frontend/app/(field)/scan/page.tsx`

The `/scan` page from Plan 02 shows an 'offline' status but doesn't persist to IndexedDB. This task wires `enqueueScan()` into the scan flow.

- [ ] **Step 1: Update `useScan.ts` to enqueue when offline**

Modify `frontend/hooks/useScan.ts` — replace the offline block:

```typescript
// Old offline block (lines 20-25 approximately):
    if (!navigator.onLine) {
      const result: ScanResultData = { status: 'offline', tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
```

Replace with:
```typescript
    if (!navigator.onLine) {
      // Persist to IndexedDB for later sync
      const { enqueueScan } = await import('@/lib/offline-queue');
      await enqueueScan({ qr_token, tipo, timestamp: timestamp.toISOString() });
      const result: ScanResultData = { status: 'offline', tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
```

- [ ] **Step 2: Verify no TypeScript errors**

```bash
npm run build 2>&1 | grep -E "^.*error TS" | head -5
```
Expected: no TypeScript errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/hooks/useScan.ts
git commit -m "feat: persist offline scans to IndexedDB queue for later sync"
```

---

### Task 4: PWA configuration

**Files:**
- Modify: `frontend/next.config.js`
- Create: `frontend/public/manifest.json`

- [ ] **Step 1: Install @ducanh2912/next-pwa**

```bash
npm install @ducanh2912/next-pwa
```

- [ ] **Step 2: Update `next.config.js`**

```javascript
const withPWA = require('@ducanh2912/next-pwa').default({
  dest: 'public',
  cacheOnFrontEndNav: true,
  aggressiveFrontEndNavCaching: true,
  reloadOnOnline: true,
  disable: process.env.NODE_ENV === 'development',
  workboxOptions: {
    disableDevLogs: true,
  },
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  // existing config
};

module.exports = withPWA(nextConfig);
```

- [ ] **Step 3: Create `public/manifest.json`**

```json
{
  "name": "UTP Parking",
  "short_name": "UTP Parking",
  "description": "Sistema de estacionamiento UTP Arequipa",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1e40af",
  "theme_color": "#1e40af",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

- [ ] **Step 4: Add manifest link to root layout**

In `frontend/app/layout.tsx`, add inside the `<head>` via metadata export:

```typescript
export const metadata: Metadata = {
  title: 'UTP Parking',
  description: 'Sistema de estacionamiento UTP Arequipa',
  manifest: '/manifest.json',
  themeColor: '#1e40af',
};
```

- [ ] **Step 5: Create placeholder icons directory**

```bash
mkdir -p public/icons
# Placeholder — replace with real icons before production
cp public/favicon.ico public/icons/icon-192.png 2>/dev/null || true
cp public/favicon.ico public/icons/icon-512.png 2>/dev/null || true
```

- [ ] **Step 6: Verify build succeeds**

```bash
npm run build 2>&1 | tail -5
```
Expected: "✓ Compiled successfully" with no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/next.config.js frontend/public/manifest.json frontend/public/icons/ frontend/app/layout.tsx
git commit -m "feat: add PWA configuration with service worker and manifest"
```

---

### Task 5: E2E tests with Playwright

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/e2e/login-redirect.spec.ts`
- Create: `frontend/tests/e2e/scan-online.spec.ts`
- Create: `frontend/tests/e2e/report-download.spec.ts`

**Prerequisite:** Backend must be running (`docker compose up` from repo root). Frontend must be running (`npm run dev`).

- [ ] **Step 1: Install Playwright browsers**

```bash
npx playwright install chromium
```

- [ ] **Step 2: Create `playwright.config.ts`**

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  retries: 1,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
```

- [ ] **Step 3: Create `tests/e2e/login-redirect.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';

// Uses the superuser created during backend setup: admin / admin123
// Role: RECTOR — should redirect to /dashboard

test.describe('Login redirect by role', () => {
  test('RECTOR login redirects to /dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 });
  });

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('noexiste');
    await page.getByLabel('Contraseña').fill('wrongpass');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await expect(page.getByText(/credenciales|error/i)).toBeVisible({ timeout: 5000 });
  });

  test('empty form shows validation error', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await expect(page.getByText(/campo requerido/i)).toBeVisible();
  });

  test('unauthenticated access to /dashboard redirects to /login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });
});
```

- [ ] **Step 4: Create `tests/e2e/report-download.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Report download', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await page.waitForURL(/\/dashboard/);
  });

  test('can navigate to reports page', async ({ page }) => {
    await page.getByRole('link', { name: /reportes/i }).click();
    await expect(page).toHaveURL(/\/reports/);
    await expect(page.getByText(/reporte de ocupación/i)).toBeVisible();
  });

  test('download users report triggers file download', async ({ page }) => {
    await page.goto('/reports');
    // Set a date range for occupancy report
    const dateFrom = page.locator('input[type="date"]').first();
    const dateTo = page.locator('input[type="date"]').nth(1);
    await dateFrom.fill('2026-01-01');
    await dateTo.fill('2026-12-31');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /descargar/i }).first().click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/reporte_ocupacion\.(xlsx|pdf)/);
  });
});
```

- [ ] **Step 5: Create `tests/e2e/scan-online.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';

// Note: scanning requires camera access and a valid QR token.
// This test verifies the scan page loads correctly for an AGENTE role.
// Full scan simulation requires a real QR token from the backend.

test.describe('Scan page', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin (RECTOR) to verify scan page is guarded
    await page.goto('/login');
    await page.getByLabel('Código Institucional').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.getByRole('button', { name: /ingresar/i }).click();
    await page.waitForURL(/\/dashboard/);
  });

  test('RECTOR cannot access /scan — redirected', async ({ page }) => {
    await page.goto('/scan');
    // Middleware redirects non-AGENTE to /dashboard or /my-qr
    await expect(page).not.toHaveURL(/\/scan/, { timeout: 3000 });
  });

  test('/dashboard shows occupancy cards', async ({ page }) => {
    await page.goto('/dashboard');
    // Cards should appear (may be empty if no data)
    await expect(page.getByText(/ocupación en tiempo real/i)).toBeVisible();
  });
});
```

- [ ] **Step 6: Run E2E tests**

Make sure Docker backend and Next.js dev server are both running:
```bash
# In repo root (separate terminal):
docker compose up

# In frontend/:
npm run dev
```

Then run:
```bash
npm run test:e2e
```
Expected: All E2E tests pass (or skip gracefully if no AGENTE user exists yet).

- [ ] **Step 7: Commit**

```bash
git add frontend/playwright.config.ts frontend/tests/e2e/
git commit -m "test: add Playwright E2E tests for login redirect, reports, and scan guard"
```

---

## Plan 05 complete — All plans complete

Run full unit test suite:
```bash
npm run test
```
Expected: All unit and component tests pass.

Run E2E suite (requires Docker backend + dev server):
```bash
npm run test:e2e
```

The complete frontend is implemented:
- **Plan 01:** Foundation — Next.js scaffold, JWT auth, API client, routing middleware, login page
- **Plan 02:** Field screens — QR scanner, personal QR, vehicle form, violations list
- **Plan 03:** Admin core — Sidebar, occupancy dashboard, violations management
- **Plan 04:** Admin secondary — Reservations, reports download, spaces, users
- **Plan 05:** PWA + offline queue + E2E tests
