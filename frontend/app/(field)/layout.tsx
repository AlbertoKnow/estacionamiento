export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <main className="flex-1 overflow-auto">{children}</main>
      {/* BottomNav — implemented in Plan 02 */}
      <nav className="h-16 bg-white border-t border-slate-200" />
    </div>
  );
}
