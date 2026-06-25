import { ScanResultData } from '@/hooks/useScan';
import { CheckCircle, XCircle, WifiOff } from 'lucide-react';

const STATUS_ICON = {
  success: { Icon: CheckCircle, color: 'text-green-500' },
  error: { Icon: XCircle, color: 'text-red-500' },
  offline: { Icon: WifiOff, color: 'text-amber-500' },
  idle: { Icon: CheckCircle, color: 'text-slate-300' },
};

export default function ScanHistory({ items }: { items: ScanResultData[] }) {
  if (!items.length) return null;
  return (
    <div className="mt-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Últimos escaneos</p>
      <ul className="space-y-1">
        {items.map((item, i) => {
          const { Icon, color } = STATUS_ICON[item.status];
          return (
            <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
              <Icon size={14} className={color} />
              <span className="flex-1 truncate">{item.nombre ?? item.message ?? 'Sin señal'}</span>
              <span className="text-xs text-slate-400">
                {item.timestamp.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
