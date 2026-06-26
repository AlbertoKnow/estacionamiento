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
