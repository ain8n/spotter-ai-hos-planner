import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';

export default function WarningsBanner({ warnings }) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div style={{ marginBottom: '1.25rem' }}>
      {warnings.map((warn, idx) => {
        const isRestart = warn.toLowerCase().includes('restart') || warn.toLowerCase().includes('34-hour');
        return (
          <div key={idx} className={`warning-banner ${isRestart ? 'restart' : ''}`}>
            {isRestart ? (
              <Info size={18} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : (
              <AlertTriangle size={18} color="#d97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            )}
            <div>
              <p style={{ fontWeight: 600 }}>{warn}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
