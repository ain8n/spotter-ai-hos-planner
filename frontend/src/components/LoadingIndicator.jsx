import React from 'react';

export default function LoadingIndicator() {
  return (
    <div className="loading-box" style={{ padding: '2.5rem 1.5rem', textAlign: 'center' }}>
      <div className="spinner-truck"></div>
      <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
        Planning…
      </h3>
    </div>
  );
}
