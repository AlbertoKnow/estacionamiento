'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useScan } from '@/hooks/useScan';
import ScanResult from '@/components/field/ScanResult';
import ScanHistory from '@/components/field/ScanHistory';

// html5-qrcode requires browser APIs — dynamic import with no SSR
const QrScanner = dynamic(() => import('@/components/field/QrScanner'), { ssr: false });

export default function ScanPage() {
  const { scan, lastResult, history } = useScan();
  const [paused, setPaused] = useState(false);
  const [tipo, setTipo] = useState<'entry' | 'exit'>('entry');

  const handleScan = useCallback(
    async (token: string) => {
      setPaused(true);
      await scan(token, tipo);
    },
    [scan, tipo]
  );

  const handleDismiss = useCallback(() => {
    setPaused(false);
  }, []);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-800">Escanear QR</h1>
        <div className="flex gap-2">
          {(['entry', 'exit'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTipo(t)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                tipo === t
                  ? 'bg-blue-700 text-white'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {t === 'entry' ? 'Entrada' : 'Salida'}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl overflow-hidden border border-slate-200 bg-black">
        <QrScanner onScan={handleScan} paused={paused} />
      </div>

      {lastResult && <ScanResult result={lastResult} onDismiss={handleDismiss} />}
      <ScanHistory items={history} />
    </div>
  );
}
