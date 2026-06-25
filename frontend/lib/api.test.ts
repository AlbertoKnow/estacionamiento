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
