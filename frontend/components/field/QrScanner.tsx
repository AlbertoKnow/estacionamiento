'use client';

import { useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';

interface Props {
  onScan: (token: string) => void;
  paused?: boolean;
}

export default function QrScanner({ onScan, paused }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const scanner = new Html5QrcodeScanner(
      'qr-reader',
      { fps: 10, qrbox: { width: 250, height: 250 }, aspectRatio: 1 },
      false
    );
    scannerRef.current = scanner;
    scanner.render(
      (text) => {
        if (!paused) onScan(text);
      },
      () => {}
    );
    return () => {
      scanner.clear().catch(() => {});
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full">
      <div ref={containerRef} id="qr-reader" className="w-full" />
    </div>
  );
}
