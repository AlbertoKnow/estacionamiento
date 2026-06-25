import ViolationList from '@/components/field/ViolationList';

export default function MyViolationsPage() {
  return (
    <div>
      <div className="p-4 border-b border-slate-200 bg-white">
        <h1 className="text-lg font-bold text-slate-800">Mis Infracciones</h1>
      </div>
      <ViolationList />
    </div>
  );
}
