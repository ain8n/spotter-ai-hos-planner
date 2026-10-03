import React, { useState } from 'react';
import PinchZoomSvgViewer from './PinchZoomSvgViewer';
import { Maximize2, X, Printer, Download, ShieldCheck } from 'lucide-react';
import { formatHours, formatMiles } from '../utils/formatters';

export default function DailyLogViewer({ logs }) {
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  if (!logs || logs.length === 0) {
    return (
      <div className="log-sheet-section" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: '#64748b' }}>No daily logs generated yet. Plan a trip above to view logs.</p>
      </div>
    );
  }

  const activeLog = logs[selectedDayIndex] || logs[0];
  const totals = activeLog.totals || {};

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadSvg = () => {
    if (!activeLog.svg_content) return;
    const blob = new Blob([activeLog.svg_content], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Drivers_Daily_Log_Day_${activeLog.day_number}_${activeLog.date}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleOpenFullscreen = () => {
    setIsFullscreen(true);
    document.body.style.overflow = 'hidden';
  };

  const handleCloseFullscreen = () => {
    setIsFullscreen(false);
    document.body.style.overflow = '';
  };

  return (
    <div className="log-sheet-section">
      {/* Top Header & Day Navigation Bar */}
      <div className="log-nav-header">
        <div>
          <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', marginBottom: '0.4rem', letterSpacing: '0.04em' }}>
            Select Day Sheet ({logs.length} Total {logs.length === 1 ? 'Day' : 'Days'})
          </div>
          <div className="day-tab-buttons">
            {logs.map((log, idx) => (
              <button
                key={idx}
                type="button"
                className={`day-tab-btn ${idx === selectedDayIndex ? 'active' : ''}`}
                onClick={() => setSelectedDayIndex(idx)}
              >
                Day {log.day_number} &bull; {log.date}
              </button>
            ))}
          </div>
        </div>

        <div className="log-actions-group">
          <button
            type="button"
            className="btn-log-action"
            style={{ background: '#2563eb', color: '#ffffff', borderColor: '#2563eb' }}
            onClick={handleOpenFullscreen}
            title="Expand to high-resolution full screen view"
          >
            <Maximize2 size={14} />
            <span>Expand Log</span>
          </button>
          <button type="button" className="btn-log-action" onClick={handleDownloadSvg}>
            <Download size={14} />
            <span>Download SVG</span>
          </button>
          <button type="button" className="btn-log-action" onClick={handlePrint}>
            <Printer size={14} />
            <span>Print Form 395</span>
          </button>
        </div>
      </div>

      {/* Daily Hours & Metrics Strip */}
      <div className="daily-totals-strip">
        <div>
          <div className="strip-item-label">1. Off Duty</div>
          <div className="strip-item-val" style={{ color: '#1e3a8a' }}>{totals.off_duty} hrs</div>
        </div>
        <div>
          <div className="strip-item-label">2. Sleeper Berth</div>
          <div className="strip-item-val" style={{ color: '#1e3a8a' }}>{totals.sleeper_berth} hrs</div>
        </div>
        <div>
          <div className="strip-item-label">3. Driving</div>
          <div className="strip-item-val" style={{ color: '#059669' }}>{totals.driving} hrs</div>
        </div>
        <div>
          <div className="strip-item-label">4. On Duty (Not Driving)</div>
          <div className="strip-item-val" style={{ color: '#d97706' }}>{totals.on_duty_not_driving} hrs</div>
        </div>
        <div>
          <div className="strip-item-label">Day Total (Must = 24.0h)</div>
          <div className="strip-item-val" style={{ color: '#0f172a' }}>= {totals.total_hours} hrs</div>
        </div>
        <div>
          <div className="strip-item-label">Daily Driving Miles</div>
          <div className="strip-item-val" style={{ color: '#2563eb' }}>{activeLog.total_miles_driving_today} mi</div>
        </div>
      </div>

      {/* Isolated SVG Log Sheet Container with Pinch-to-Zoom & Pan (No page zooming or page overflow) */}
      <div className="log-canvas-scroll-wrapper">
        <PinchZoomSvgViewer svgContent={activeLog.svg_content} />
      </div>

      {/* Full-Screen Expand Modal with Pinch Zoom */}
      {isFullscreen && (
        <div className="fullscreen-modal-overlay">
          <div className="fullscreen-modal-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={20} color="#60a5fa" />
              <span style={{ fontSize: '1rem', fontWeight: 800 }}>
                Day {activeLog.day_number} &bull; {activeLog.date_formatted || activeLog.date} &bull; Driver's Daily Log (Form 395)
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn-log-action"
                style={{ background: '#2563eb', color: '#ffffff' }}
                onClick={handlePrint}
              >
                <Printer size={14} /> Print
              </button>
              <button
                type="button"
                className="btn-log-action"
                onClick={handleCloseFullscreen}
              >
                <X size={16} /> Close
              </button>
            </div>
          </div>
          <div className="fullscreen-modal-body">
            <PinchZoomSvgViewer svgContent={activeLog.svg_content} />
          </div>
        </div>
      )}
    </div>
  );
}
