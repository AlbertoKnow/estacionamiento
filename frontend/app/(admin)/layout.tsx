export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar — implemented in Plan 03 */}
      <aside className="w-64 bg-white border-r border-slate-200 flex-shrink-0">
        <div className="p-4 font-semibold text-slate-800">UTP Parking</div>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
