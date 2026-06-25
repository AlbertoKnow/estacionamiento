import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

const mockLogin = vi.fn();
const mockPush = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin, user: null, isLoading: false }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset document.cookie between tests
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
  });

  it('renders codigo and password fields', () => {
    render(<LoginForm />);
    expect(screen.getByLabelText(/código institucional/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
  });

  it('shows validation error when fields are empty', async () => {
    render(<LoginForm />);
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/campo requerido/i)).toBeInTheDocument();
  });

  it('calls login with form values on submit', async () => {
    mockLogin.mockResolvedValue(undefined);
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText(/código institucional/i), 'ALU001');
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'pass123');
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('ALU001', 'pass123'));
  });

  it('shows error message on login failure', async () => {
    mockLogin.mockRejectedValue({
      response: { data: { detail: 'Credenciales inválidas.' } },
    });
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText(/código institucional/i), 'ALU001');
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'wrong');
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/credenciales inválidas/i)).toBeInTheDocument();
  });
});
