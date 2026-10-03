import React, { useState } from 'react';
import { Navigation2, CornerDownRight, Clock, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { formatMiles, formatDateTime, formatHours } from '../utils/formatters';

export default function RouteDirections({ instructions, timeline, timezone }) {
  const leg1 = instructions?.leg1_current_to_pickup;
  const leg2 = instructions?.leg2_pickup_to_dropoff;

  const [tableZoom, setTableZoom] = useState(1.0);

  const handleZoomIn = () => {
    setTableZoom((prev) => Math.min(2.0, Number((prev + 0.2).toFixed(1))));
  };

  const handleZoomOut = () => {
    setTableZoom((prev) => Math.max(0.7, Number((prev - 0.2).toFixed(1))));
  };

  const handleResetZoom = () => {
    setTableZoom(1.0);
  };

  return (
    <div>
      {/* 2 Legs Directions Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        {/* Leg 1 */}
        {leg1 && (
          <div className="planner-card" style={{ padding: '1.25rem', margin: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Navigation2 size={18} color="#0d9488" />
              <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>
                Leg 1: Current &rarr; Pickup (Approach)
              </h4>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1rem' }}>
              <div><strong>From:</strong> {leg1.from}</div>
              <div><strong>To:</strong> {leg1.to}</div>
              <div style={{ color: '#0d9488', fontWeight: 700, marginTop: '2px' }}>
                Distance: {formatMiles(leg1.distance_miles)}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {leg1.steps && leg1.steps.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    padding: '0.6rem',
                    background: '#f8fafc',
                    borderRadius: '6px',
                    border: '1px solid #e2e8f0',
                    fontSize: '0.82rem'
                  }}
                >
                  <CornerDownRight size={14} color="#64748b" style={{ flexShrink: 0, marginTop: '3px' }} />
                  <div>
                    <div style={{ fontWeight: 600, color: '#1e293b' }}>{step.text}</div>
                    <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                      {step.distance_miles} mi &bull; ~{step.duration_mins} mins
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Leg 2 */}
        {leg2 && (
          <div className="planner-card" style={{ padding: '1.25rem', margin: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Navigation2 size={18} color="#2563eb" />
              <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>
                Leg 2: Pickup &rarr; Drop-off (Loaded Freight)
              </h4>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1rem' }}>
              <div><strong>From:</strong> {leg2.from}</div>
              <div><strong>To:</strong> {leg2.to}</div>
              <div style={{ color: '#2563eb', fontWeight: 700, marginTop: '2px' }}>
                Distance: {formatMiles(leg2.distance_miles)}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {leg2.steps && leg2.steps.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.5rem',
                    padding: '0.6rem',
                    background: '#f8fafc',
                    borderRadius: '6px',
                    border: '1px solid #e2e8f0',
                    fontSize: '0.82rem'
                  }}
                >
                  <CornerDownRight size={14} color="#64748b" style={{ flexShrink: 0, marginTop: '3px' }} />
                  <div>
                    <div style={{ fontWeight: 600, color: '#1e293b' }}>{step.text}</div>
                    <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                      {step.distance_miles} mi &bull; ~{step.duration_mins} mins
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chronological Timeline Table */}
      {timeline && timeline.length > 0 && (
        <div className="planner-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={16} color="#2563eb" />
              <span>Complete Duty Status Event Log</span>
            </h4>
            
            {/* Mobile / Desktop Zoom Control Bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.78rem', color: '#64748b', marginRight: '4px' }}>
                {timeline.length} Events
              </span>
              <button
                type="button"
                className="btn-pinch-ctrl"
                onClick={handleZoomOut}
                disabled={tableZoom <= 0.7}
                title="Zoom Out (−)"
                style={{ width: '26px', height: '26px', border: '1px solid #cbd5e1' }}
              >
                <ZoomOut size={13} />
              </button>
              <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono', fontWeight: 700, minWidth: '35px', textAlign: 'center' }}>
                {Math.round(tableZoom * 100)}%
              </span>
              <button
                type="button"
                className="btn-pinch-ctrl"
                onClick={handleZoomIn}
                disabled={tableZoom >= 2.0}
                title="Zoom In (+)"
                style={{ width: '26px', height: '26px', border: '1px solid #cbd5e1' }}
              >
                <ZoomIn size={13} />
              </button>
              {tableZoom !== 1.0 && (
                <button
                  type="button"
                  className="btn-pinch-ctrl btn-reset-zoom"
                  onClick={handleResetZoom}
                  title="Reset to 100%"
                  style={{ height: '26px', border: '1px solid #cbd5e1' }}
                >
                  <RotateCcw size={11} />
                  <span>100%</span>
                </button>
              )}
            </div>
          </div>

          <div style={{ overflowX: 'auto', width: '100%', WebkitOverflowScrolling: 'touch' }}>
            <table
              className="stops-table"
              style={{
                width: '100%',
                fontSize: `${0.82 * tableZoom}rem`,
                transformOrigin: '0 0',
                transition: 'font-size 0.15s ease',
              }}
            >
              <thead>
                <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>#</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>Start Time</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>End Time</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>Duration</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>Duty Status</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>Activity</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>Location</th>
                  <th style={{ padding: `${0.5 * tableZoom}rem` }}>Odometer</th>
                </tr>
              </thead>
              <tbody>
                {timeline.map((ev, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <td style={{ padding: `${0.5 * tableZoom}rem`, fontWeight: 700, color: '#94a3b8' }}>{ev.id}</td>
                    <td style={{ padding: `${0.5 * tableZoom}rem` }}>{formatDateTime(ev.start_time, timezone)}</td>
                    <td style={{ padding: `${0.5 * tableZoom}rem` }}>{formatDateTime(ev.end_time, timezone)}</td>
                    <td style={{ padding: `${0.5 * tableZoom}rem`, fontWeight: 700 }}>{formatHours(ev.duration_hours)}</td>
                    <td style={{ padding: `${0.5 * tableZoom}rem` }}>
                      <span style={{
                        display: 'inline-block',
                        padding: `${0.15 * tableZoom}rem ${0.45 * tableZoom}rem`,
                        borderRadius: '4px',
                        fontSize: `${0.72 * tableZoom}rem`,
                        fontWeight: 700,
                        backgroundColor: ev.status === 'DRIVING' ? '#ecfdf5' : ev.status === 'ON_DUTY_NOT_DRIVING' ? '#fffbeb' : '#eff6ff',
                        color: ev.status === 'DRIVING' ? '#059669' : ev.status === 'ON_DUTY_NOT_DRIVING' ? '#d97706' : '#1e3a8a',
                      }}>
                        {ev.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ padding: `${0.5 * tableZoom}rem`, fontWeight: 600 }}>{ev.activity_type}</td>
                    <td style={{ padding: `${0.5 * tableZoom}rem` }}>{ev.location_name}</td>
                    <td style={{ padding: `${0.5 * tableZoom}rem`, fontFamily: 'JetBrains Mono' }}>{ev.end_odometer} mi</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
