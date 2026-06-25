import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import VehicleForm from './VehicleForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockMutate = vi.fn();
vi.mock('@/hooks/useMyVehicle', () => ({
  useMyVehicle: () => ({ data: null, isLoading: false }),
  useUpsertVehicle: () => ({ mutateAsync: mockMutate, isPending: false }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      {children}
    </QueryClientProvider>
  );
}

describe('VehicleForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders placa and tipo fields', () => {
    render(<VehicleForm />, { wrapper });
    expect(screen.getByLabelText(/placa/i)).toBeInTheDocument();
  });

  it('validates placa format', async () => {
    render(<VehicleForm />, { wrapper });
    await userEvent.type(screen.getByLabelText(/placa/i), 'INVALID');
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }));
    expect(await screen.findByText(/formato de placa inválido/i)).toBeInTheDocument();
  });

  it('submits valid placa', async () => {
    mockMutate.mockResolvedValue({});
    render(<VehicleForm />, { wrapper });
    await userEvent.type(screen.getByLabelText(/placa/i), 'ABC-123');
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }));
    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(expect.objectContaining({ placa: 'ABC-123' }))
    );
  });
});
