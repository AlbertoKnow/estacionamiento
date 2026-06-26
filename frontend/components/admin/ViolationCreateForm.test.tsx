import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ViolationCreateForm from './ViolationCreateForm';

const mockMutate = vi.fn();

vi.mock('@/hooks/useViolations', () => ({
  useViolationTypes: () => ({
    data: [
      { id: 1, nombre: 'Estacionar en zona prohibida', nivel: 'leve', descripcion: '' },
      { id: 2, nombre: 'Conducción temeraria', nivel: 'grave', descripcion: '' },
    ],
    isLoading: false,
  }),
  useCreateViolation: () => ({ mutate: mockMutate, isPending: false }),
}));

describe('ViolationCreateForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders user_id input, violation type select, and submit button', () => {
    render(<ViolationCreateForm onSuccess={() => {}} />);
    expect(screen.getByLabelText(/id de usuario/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/tipo de falta/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /registrar infracción/i })).toBeInTheDocument();
  });

  it('shows error when submitting without required fields', async () => {
    const { container } = render(<ViolationCreateForm onSuccess={() => {}} />);
    // fireEvent.submit bypasses native HTML constraint validation so handleSubmit runs
    fireEvent.submit(container.querySelector('form')!);
    expect(await screen.findByText(/usuario y tipo de falta son obligatorios/i)).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('shows error when only user_id is filled but no violation type selected', async () => {
    const { container } = render(<ViolationCreateForm onSuccess={() => {}} />);
    await userEvent.type(screen.getByLabelText(/id de usuario/i), '42');
    // fireEvent.submit bypasses native HTML constraint validation so handleSubmit runs
    fireEvent.submit(container.querySelector('form')!);
    expect(await screen.findByText(/usuario y tipo de falta son obligatorios/i)).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('calls createViolation with correct data on valid submit', async () => {
    render(<ViolationCreateForm onSuccess={() => {}} />);
    await userEvent.type(screen.getByLabelText(/id de usuario/i), '42');
    fireEvent.change(screen.getByLabelText(/tipo de falta/i), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: /registrar infracción/i }));
    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(
        { user_id: 42, tipo_falta_id: 1, descripcion: undefined },
        expect.objectContaining({
          onSuccess: expect.any(Function),
          onError: expect.any(Function),
        })
      )
    );
  });

  it('calls onSuccess callback after successful creation', async () => {
    const onSuccess = vi.fn();
    mockMutate.mockImplementation((_data: unknown, options?: { onSuccess?: () => void }) =>
      options?.onSuccess?.()
    );
    render(<ViolationCreateForm onSuccess={onSuccess} />);
    await userEvent.type(screen.getByLabelText(/id de usuario/i), '5');
    fireEvent.change(screen.getByLabelText(/tipo de falta/i), { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: /registrar infracción/i }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
  });
});
