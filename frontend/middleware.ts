import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const REFRESH_COOKIE = 'utp_refresh';
const ROLE_COOKIE = 'utp_role';

const FIELD_ROLES = new Set(['agente_seguridad', 'alumno', 'academico', 'administrativo']);
const ADMIN_ONLY_PATHS = ['/dashboard', '/reservations', '/reports', '/spaces', '/users', '/violations'];
const AGENT_PATH = '/scan';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (
    pathname.startsWith('/login') ||
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/icons/') ||
    pathname === '/manifest.json' ||
    pathname === '/favicon.ico' ||
    /\/(sw\.js|workbox-[^/]+\.js)$/.test(pathname)
  ) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.has(REFRESH_COOKIE);
  if (!hasSession) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  const role = request.cookies.get(ROLE_COOKIE)?.value ?? '';

  if (ADMIN_ONLY_PATHS.some((p) => pathname.startsWith(p)) && FIELD_ROLES.has(role)) {
    const dest = role === 'agente_seguridad' ? '/scan' : '/my-qr';
    return NextResponse.redirect(new URL(dest, request.url));
  }

  if (pathname.startsWith(AGENT_PATH) && role !== 'agente_seguridad') {
    return NextResponse.redirect(new URL('/my-qr', request.url));
  }

  if (
    (pathname.startsWith('/my-qr') ||
      pathname.startsWith('/my-vehicle') ||
      pathname.startsWith('/my-violations')) &&
    !FIELD_ROLES.has(role)
  ) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
