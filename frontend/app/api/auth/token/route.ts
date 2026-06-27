import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_URL = process.env.API_URL ?? 'http://localhost:8000/api/v1';
const COOKIE_NAME = 'utp_refresh';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7; // 7 days

// GET → use stored refresh cookie to get new access token from Django
export async function GET() {
  const cookieStore = cookies();
  const refresh = cookieStore.get(COOKIE_NAME)?.value;
  if (!refresh) {
    return NextResponse.json({ detail: 'No refresh token' }, { status: 401 });
  }
  const res = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    const response = NextResponse.json({ detail: 'Token refresh failed' }, { status: 401 });
    response.cookies.delete(COOKIE_NAME);
    return response;
  }
  const data = await res.json();
  return NextResponse.json({ access: data.access });
}

// POST → store refresh token in httpOnly cookie
export async function POST(request: Request) {
  const { refresh } = await request.json();
  const response = NextResponse.json({ ok: true });
  response.cookies.set(COOKIE_NAME, refresh, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: COOKIE_MAX_AGE,
    path: '/',
  });
  return response;
}

// DELETE → blacklist refresh token server-side, then clear cookies (logout)
export async function DELETE() {
  const cookieStore = cookies();
  const refresh = cookieStore.get(COOKIE_NAME)?.value;

  if (refresh) {
    try {
      await fetch(`${API_URL}/auth/logout/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
    } catch {
      // Fire-and-forget — proceed with local cleanup even if backend fails
    }
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.delete(COOKIE_NAME);
  response.cookies.delete('utp_role');
  return response;
}
