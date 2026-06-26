'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ROLE_REDIRECTS: Record<string, string> = {
  agente_seguridad: '/scan',
  alumno: '/my-qr',
  academico: '/my-qr',
  administrativo: '/my-qr',
  jefe_operaciones: '/dashboard',
  jefe_seguridad: '/dashboard',
  asistente_operaciones: '/dashboard',
  director: '/dashboard',
  rector: '/dashboard',
};

export default function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [codigo, setCodigo] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setFieldError('');
    if (!codigo.trim() || !password.trim()) {
      setFieldError('Campo requerido');
      return;
    }
    setIsLoading(true);
    try {
      await login(codigo.trim(), password);
      const role = document.cookie.match(/utp_role=([^;]+)/)?.[1] ?? '';
      router.push(ROLE_REDIRECTS[role] ?? '/dashboard');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al iniciar sesión.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-center text-2xl">UTP Parking</CardTitle>
        <p className="text-center text-sm text-muted-foreground">Arequipa — Sótano 2 y 3</p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="codigo">Código Institucional</Label>
            <Input
              id="codigo"
              type="text"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="ALU001"
              autoComplete="username"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="password">Contraseña</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {fieldError && <p className="text-sm text-destructive">{fieldError}</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Ingresando...' : 'Ingresar'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
