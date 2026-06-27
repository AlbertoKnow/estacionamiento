import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./auth', () => ({
  getAccessToken: vi.fn(() => 'mock-access-token'),
  setAccessToken: vi.fn(),
  clearAccessToken: vi.fn(),
}));

global.fetch = vi.fn();

describe('api client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('exports a default axios instance', async () => {
    const { default: api } = await import('./api');
    expect(api).toBeDefined();
    expect(typeof api.get).toBe('function');
    expect(typeof api.post).toBe('function');
  });

  it('has baseURL configured', async () => {
    const { default: api } = await import('./api');
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api/v1');
  });
});

// ---------------------------------------------------------------------------
// 401 refresh interceptor tests
// ---------------------------------------------------------------------------
// Helper type for the internal axios interceptor handler list.
type InterceptorHandler = { fulfilled?: unknown; rejected?: (err: unknown) => Promise<unknown> };

/**
 * Returns the rejection handler registered by api.ts on the response interceptor.
 * We access the internal `handlers` array so we can invoke the logic in isolation
 * without needing a running HTTP server.
 */
async function getInterceptorHandler() {
  const { default: api } = await import('./api');
  const handlers: InterceptorHandler[] = (api.interceptors.response as unknown as { handlers: InterceptorHandler[] }).handlers;
  const entry = handlers.find((h) => typeof h?.rejected === 'function');
  if (!entry?.rejected) throw new Error('Interceptor rejection handler not found');
  return { api, rejected: entry.rejected };
}

describe('401 refresh interceptor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('is registered on the api instance with a rejection handler', async () => {
    const { api } = await getInterceptorHandler();
    const handlers: InterceptorHandler[] = (api.interceptors.response as unknown as { handlers: InterceptorHandler[] }).handlers;
    expect(handlers.some((h) => typeof h?.rejected === 'function')).toBe(true);
  });

  it('passes non-401 errors through without calling /api/auth/token', async () => {
    const { rejected } = await getInterceptorHandler();
    const err = { response: { status: 500 }, config: { headers: {}, _retry: false } };
    await expect(rejected(err)).rejects.toEqual(err);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('_retry guard: does not call /api/auth/token for already-retried 401 (loop guard)', async () => {
    const { rejected } = await getInterceptorHandler();
    const err = { response: { status: 401 }, config: { headers: {}, _retry: true } };
    await expect(rejected(err)).rejects.toEqual(err);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('refresh failure: clears access token and redirects to /login', async () => {
    const { clearAccessToken } = await import('./auth');
    const { rejected } = await getInterceptorHandler();

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ ok: false });

    // jsdom does not implement navigation, so we swap window.location with a
    // plain writable object to capture the href assignment without throwing.
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      configurable: true,
      writable: true,
    });

    const err = { response: { status: 401 }, config: { headers: {} } };
    await expect(rejected(err)).rejects.toThrow('refresh_failed');

    expect(global.fetch).toHaveBeenCalledWith('/api/auth/token');
    expect(clearAccessToken).toHaveBeenCalled();
    expect(window.location.href).toBe('/login');

    // Restore original location so subsequent tests are not affected
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      configurable: true,
      writable: true,
    });
  });

  it('concurrent 401s: only one /api/auth/token call, second request queued', async () => {
    const { setAccessToken } = await import('./auth');
    const { rejected } = await getInterceptorHandler();

    // Deferred fetch — lets us control when the refresh resolves so we can
    // enqueue a second 401 while the first refresh is still in-flight.
    let resolveRefresh!: (r: unknown) => void;
    const refreshPromise = new Promise((res) => { resolveRefresh = res; });
    (global.fetch as ReturnType<typeof vi.fn>).mockImplementationOnce(() => refreshPromise);

    const err1 = { response: { status: 401 }, config: { headers: {} } };
    const err2 = { response: { status: 401 }, config: { headers: {} } };

    // Start both handlers; synchronous execution inside the async function runs
    // up to the first `await fetch(...)`, so isRefreshing is set to true before
    // rejected(err2) runs — err2 gets queued instead of triggering a second fetch.
    const p1 = rejected(err1);
    const p2 = rejected(err2);

    // Resolve the single refresh call
    resolveRefresh({ ok: true, json: async () => ({ access: 'queued-token' }) });

    // Both promises settle (may reject with network errors when replaying via
    // XHR in jsdom, but that is irrelevant — we only care about fetch call count).
    await Promise.allSettled([p1, p2]);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('/api/auth/token');
    expect(setAccessToken).toHaveBeenCalledWith('queued-token');
  });
});

/*
 * Full-coverage note
 * ------------------
 * The three tests above cover the highest-risk paths:
 *   1. Non-401 / _retry pass-through (loop guard)
 *   2. Refresh failure → token clear + redirect
 *   3. Concurrent 401 queue (only one refresh call)
 *
 * To add a "successful refresh replays the request with new token" test,
 * the easiest approach is axios-mock-adapter:
 *
 *   import MockAdapter from 'axios-mock-adapter';
 *   const mock = new MockAdapter(api);
 *   mock.onGet('/protected').replyOnce(401).onGet('/protected').reply(200, { ok: true });
 *   (global.fetch as any).mockResolvedValueOnce({ ok: true, json: async () => ({ access: 'tok' }) });
 *   const res = await api.get('/protected');
 *   expect(res.data).toEqual({ ok: true });
 *   expect(setAccessToken).toHaveBeenCalledWith('tok');
 *
 * This requires `npm install -D axios-mock-adapter` — not yet in the project.
 */
