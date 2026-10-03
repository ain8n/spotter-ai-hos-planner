import React from 'react';

export default function SvgLogSheet({ svgContent }) {
  if (!svgContent) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
        No log sheet generated yet.
      </div>
    );
  }

  return (
    <div
      className="svg-render-box"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
}
