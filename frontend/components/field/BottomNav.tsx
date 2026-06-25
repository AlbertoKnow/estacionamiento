'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { QrCode, ScanLine, Car, AlertCircle } from 'lucide-react';

const AGENT_ITEMS = [
  { href: '/scan', label: 'Escanear', icon: ScanLine },
];

const USER_ITEMS = [
  { href: '/my-qr', label: 'Mi QR', icon: QrCode },
  { href: '/my-vehicle', label: 'Vehículo', icon: Car },
  { href: '/my-violations', label: 'Infracciones', icon: AlertCircle },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user?.rol === 'AGENTE' ? AGENT_ITEMS : USER_ITEMS;

  return (
    <nav className="h-16 bg-white border-t border-slate-200 flex items-center">
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`flex-1 flex flex-col items-center justify-center gap-0.5 text-xs ${
              active ? 'text-blue-700 font-semibold' : 'text-slate-500'
            }`}
          >
            <Icon size={20} strokeWidth={active ? 2.5 : 1.5} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
