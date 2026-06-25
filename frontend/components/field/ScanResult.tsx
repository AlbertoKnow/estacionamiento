'use client';

import { useEffect, useState } from 'react';
import { ScanResultData } from '@/hooks/useScan';
import { CheckCircle, XCircle, WifiOff } from 'lucide-react';

interface Props {
  result: ScanResultData;
  onDismiss: () => void;
}

const CONFIG = {
  success: {
    bg: 'bg-green-50 border-green-200',
    text: 'text-green-800',
    icon: CheckCircle,
    iconColor: 'text-green-600',
  },
  error: {
    bg: 'bg-red-50 border-red-200',
    text: 'text-red-800',
    icon: XCircle,
    iconColor: 'text-red-600',
  },
  offline: {
    bg: 'bg-amber-50 border-amber-200',
    text: 'text-amber-800',
    icon: WifiOff,
    iconColor: 'text-amber-600',
  },
  idle: {
    bg: 'bg-slate-50 border-slate-200',
    text: 'text-slate-800',
    icon: CheckCircle,
    iconColor: 'text-slate-400',
  },
};

export default function ScanResult({ result, onDismiss }: Props) {
  const [visible, setVisible] = useState(true);
  const cfg = CONFIG[result.status];
  const Icon = cfg.icon;

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300);
    }, 4000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const label =
    result.status === 'success'
      ? `${result.tipo === 'entry' ? 'ENTRADA' : 'SALIDA'} REGISTRADA`
      : result.status === 'offline'
      ? 'REGISTRADO LOCALMENTE'
      : 'ACCESO DENEGADO';

  return (
    <div
      className={`transition-opacity duration-300 ${visible ? 'opacity-100' : 'opacity-0'} border rounded-xl p-4 ${cfg.bg}`}
    >
      <div className="flex items-center gap-3">
        <Icon size={32} className={cfg.iconColor} />
        <div>
          <p className={`font-bold text-lg ${cfg.text}`}>{label}</p>
          {result.nombre && (
            <p className={`text-sm ${cfg.text}`}>
              {result.nombre} · {result.placa}
            </p>
          )}
          {result.message && <p className={`text-sm ${cfg.text}`}>{result.message}</p>}
          {result.status === 'offline' && (
            <p className={`text-xs ${cfg.text} mt-1`}>
              Se sincronizará al recuperar señal
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
