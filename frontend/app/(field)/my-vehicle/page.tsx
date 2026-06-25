import VehicleForm from '@/components/field/VehicleForm';

export default function MyVehiclePage() {
  return (
    <div>
      <div className="p-4 border-b border-slate-200 bg-white">
        <h1 className="text-lg font-bold text-slate-800">Mi Vehículo</h1>
      </div>
      <VehicleForm />
    </div>
  );
}
