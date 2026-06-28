import Dexie, { Table } from 'dexie';
import api from './api';

export interface PendingScan {
  id?: number;
  token: string;
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
  data: Pick<PendingScan, 'token' | 'tipo' | 'timestamp'>
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
      token: s.token,
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
