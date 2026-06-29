import BottomNav from '@/components/field/BottomNav';
import OfflineBanner from '@/components/shared/OfflineBanner';

export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-50 max-w-lg mx-auto w-full">
      <OfflineBanner />
      <main className="flex-1 overflow-auto">{children}</main>
      <BottomNav />
    </div>
  );
}
