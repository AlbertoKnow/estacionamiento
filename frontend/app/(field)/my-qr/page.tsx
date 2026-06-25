import QrDisplay from '@/components/field/QrDisplay';
import Link from 'next/link';

export default function MyQrPage() {
  return (
    <div className="p-4">
      <h1 className="text-lg font-bold text-slate-800 mb-4 text-center">Mi Código QR</h1>
      <QrDisplay />
      <p className="text-center text-xs text-slate-400 mt-4">
        Muestra este código al agente de seguridad en el ingreso
      </p>
      <div className="mt-4 text-center">
        <Link href="/my-vehicle" className="text-sm text-blue-700 underline">
          Gestionar vehículo
        </Link>
      </div>
    </div>
  );
}
