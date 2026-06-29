'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import {
  setAccessToken,
  clearAccessToken,
  storeRefreshCookie,
  refreshAccessToken,
} from '@/lib/auth';

export interface AuthUser {
  id: number;
  codigo_institucional: string;
  nombre: string;
  apellido: string;
  rol: string;
  campus_asignado: { id: number; nombre: string } | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (codigo: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    refreshAccessToken()
      .then(() => api.get<AuthUser>('/users/me/').then((r) => setUser(r.data)))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (codigo: string, password: string): Promise<AuthUser> => {
    const res = await api.post<{ access: string; refresh: string; user: AuthUser }>(
      '/auth/login/',
      { codigo_institucional: codigo, password }
    );
    setAccessToken(res.data.access);
    await storeRefreshCookie(res.data.refresh, res.data.user.rol);
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch('/api/auth/token', { method: 'DELETE' });
    } catch {
      // fire-and-forget
    } finally {
      clearAccessToken();
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
