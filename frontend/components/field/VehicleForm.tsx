'use client';

import { useState, useEffect } from 'react';
import { useMyVehicle, useUpsertVehicle } from '@/hooks/useMyVehicle';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const PLACA_REGEX = /^[A-Z0-9]{3}-?[A-Z0-9]{3}$/i;
const TIPOS = ['AUTO', 'CAMIONETA', 'MOTO', 'OTRO'];

export default function VehicleForm() {
  const { data: vehicle } = useMyVehicle();
  const { mutateAsync, isPending } = useUpsertVehicle();

  const [placa, setPlaca] = useState('');
  const [tipo, setTipo] = useState('AUTO');
  const [marca, setMarca] = useState('');
  const [modelo, setModelo] = useState('');
  const [color, setColor] = useState('');
  const [placaError, setPlacaError] = useState('');

  useEffect(() => {
    if (vehicle) {
      setPlaca(vehicle.placa);
      setTipo(vehicle.tipo);
      setMarca(vehicle.marca ?? '');
      setModelo(vehicle.modelo ?? '');
      setColor(vehicle.color ?? '');
    }
  }, [vehicle]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPlacaError('');
    if (!PLACA_REGEX.test(placa)) {
      setPlacaError('Formato de placa inválido (ej: ABC-123)');
      return;
    }
    try {
      await mutateAsync({ id: vehicle?.id, placa: placa.toUpperCase(), tipo, marca, modelo, color });
      toast.success('Vehículo guardado correctamente');
    } catch {
      toast.error('Error al guardar el vehículo');
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4">
      <div>
        <Label htmlFor="placa">Placa</Label>
        <Input
          id="placa"
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          placeholder="ABC-123"
          className="uppercase"
        />
        {placaError && <p className="text-sm text-destructive mt-1">{placaError}</p>}
      </div>
      <div>
        <Label htmlFor="tipo">Tipo de vehículo</Label>
        <select
          id="tipo"
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="w-full h-10 px-3 border border-input rounded-md text-sm bg-background"
        >
          {TIPOS.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="marca">Marca</Label>
        <Input id="marca" value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Toyota" />
      </div>
      <div>
        <Label htmlFor="modelo">Modelo (opcional)</Label>
        <Input id="modelo" value={modelo} onChange={(e) => setModelo(e.target.value)} placeholder="Corolla" />
      </div>
      <div>
        <Label htmlFor="color">Color (opcional)</Label>
        <Input id="color" value={color} onChange={(e) => setColor(e.target.value)} placeholder="Blanco" />
      </div>
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? 'Guardando...' : 'Guardar vehículo'}
      </Button>
    </form>
  );
}
