let _accessToken: string | null = null;

export const setAccessToken = (token: string): void => {
  _accessToken = token;
};

export const getAccessToken = (): string | null => _accessToken;

export const clearAccessToken = (): void => {
  _accessToken = null;
};

export async function storeRefreshCookie(refresh: string): Promise<void> {
  await fetch('/api/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
}

export async function refreshAccessToken(): Promise<string> {
  const res = await fetch('/api/auth/token', { method: 'GET' });
  if (!res.ok) throw new Error('refresh_failed');
  const data = await res.json();
  setAccessToken(data.access);
  return data.access;
}

export async function clearRefreshCookie(): Promise<void> {
  await fetch('/api/auth/token', { method: 'DELETE' });
  clearAccessToken();
}
