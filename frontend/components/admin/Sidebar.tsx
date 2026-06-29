'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard,
  AlertTriangle,
  CalendarClock,
  FileBarChart,
  ParkingSquare,
  Users,
  LogOut,
} from 'lucide-react';
import { toast } from 'sonner';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['asistente_operaciones', 'jefe_operaciones', 'jefe_seguridad', 'director', 'rector'] },
  { href: '/violations', label: 'Infracciones', icon: AlertTriangle, roles: ['asistente_operaciones', 'jefe_operaciones', 'jefe_seguridad', 'director', 'rector'] },
  { href: '/reservations', label: 'Reservas', icon: CalendarClock, roles: ['jefe_operaciones', 'director', 'rector'] },
  { href: '/reports', label: 'Reportes', icon: FileBarChart, roles: ['jefe_seguridad', 'jefe_operaciones', 'director', 'rector'] },
  { href: '/spaces', label: 'Espacios', icon: ParkingSquare, roles: ['jefe_operaciones', 'jefe_seguridad', 'director', 'rector'] },
  { href: '/users', label: 'Usuarios', icon: Users, roles: ['jefe_operaciones', 'jefe_seguridad', 'director', 'rector'] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  const visibleItems = NAV_ITEMS.filter(
    (item) => user?.rol && item.roles.includes(user.rol)
  );

  async function handleLogout() {
    await logout();
    toast.success('Sesión cerrada');
    router.push('/login');
  }

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-full">
      <div className="p-5 border-b border-slate-100">
        <p className="font-bold text-blue-800 text-lg">UTP Parking</p>
        <p className="text-xs text-slate-400">Arequipa — Sótano 2 y 3</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {visibleItems.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-50 text-blue-800'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-100">
        <p className="text-xs font-semibold text-slate-700 truncate">
          {user?.nombre} {user?.apellido}
        </p>
        <p className="text-xs text-slate-400 truncate">{user?.rol?.replace('_', ' ')}</p>
        <button
          onClick={handleLogout}
          className="mt-3 flex items-center gap-2 text-xs text-slate-500 hover:text-red-600 transition-colors"
        >
          <LogOut size={14} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
