import BottomNav from '@/components/field/BottomNav';

export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-50 max-w-md mx-auto">
      <main className="flex-1 overflow-auto">{children}</main>
      <BottomNav />
    </div>
  );
}
