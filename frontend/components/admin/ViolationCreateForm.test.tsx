import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ViolationCreateForm from './ViolationCreateForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockCreate = vi.fn();
vi.mock('@/hooks/useViolations', () => ({
  useViolationTypes: () => ({
    data: [
      { id: 1, nombre: 'Estacionar en zona prohibida', nivel: 'leve' },
      { id: 2, nombre: 'Conducción temeraria', nivel: 'grave' },
    ],
  }),
  useCreateViolation: () => ({ mutateAsync: mockCreate, isPending: false }),
}));

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: [{ codigo_institucional: 'ALU001', nombre: 'Ana', apellido: 'García', id: 5 }],
    }),
  },
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
}

describe('ViolationCreateForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders user search and violation type fields', () => {
    render(<ViolationCreateForm onSuccess={() => {}} />, { wrapper });
    expect(screen.getByPlaceholderText(/código institucional/i)).toBeInTheDocument();
  });

  it('requires a violation type before submit', async () => {
    render(<ViolationCreateForm onSuccess={() => {}} />, { wrapper });
    fireEvent.click(screen.getByRole('button', { name: /registrar/i }));
    expect(await screen.findByText(/selecciona un tipo de falta/i)).toBeInTheDocument();
  });
});
