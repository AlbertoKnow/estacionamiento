import { describe, it, expect, beforeEach } from 'vitest';
import { setAccessToken, getAccessToken, clearAccessToken } from './auth';

describe('auth token management', () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it('returns null when no token set', () => {
    expect(getAccessToken()).toBeNull();
  });

  it('stores and retrieves access token', () => {
    setAccessToken('test-token-abc');
    expect(getAccessToken()).toBe('test-token-abc');
  });

  it('clears access token', () => {
    setAccessToken('test-token-abc');
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });

  it('overwrites existing token', () => {
    setAccessToken('token-1');
    setAccessToken('token-2');
    expect(getAccessToken()).toBe('token-2');
  });
});
