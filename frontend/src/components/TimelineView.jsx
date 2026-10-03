import React from 'react';
import { formatTimeOnly, formatHours, formatDateTime } from '../utils/formatters';
import { Clock, Navigation, CheckCircle2 } from 'lucide-react';

export default function TimelineView({ timeline }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: '#64748b' }}>No timeline events recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Clock size={18} color="#2563eb" />
          <span>Chronological Duty Status Timeline</span>
        </h3>
        <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
          {timeline.length} Total Events
        </span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="stops-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>Duration</th>
              <th>Duty Status</th>
              <th>Activity</th>
              <th>Location</th>
              <th>Odometer</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {timeline.map((ev, idx) => {
              let statColor = '#64748b';
              let statBg = '#f1f5f9';
              if (ev.status === 'DRIVING') {
                statColor = '#059669';
                statBg = '#ecfdf5';
              } else if (ev.status === 'ON_DUTY_NOT_DRIVING') {
                statColor = '#d97706';
                statBg = '#fffbeb';
              } else if (ev.status === 'SLEEPER_BERTH') {
                statColor = '#4338ca';
                statBg = '#e0e7ff';
              }

              return (
                <tr key={idx}>
                  <td style={{ fontWeight: 700, color: '#94a3b8' }}>{ev.id}</td>
                  <td style={{ fontWeight: 600 }}>{formatDateTime(ev.start_time)}</td>
                  <td style={{ fontWeight: 600 }}>{formatDateTime(ev.end_time)}</td>
                  <td style={{ fontWeight: 700 }}>{formatHours(ev.duration_hours)}</td>
                  <td>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: statBg,
                      color: statColor
                    }}>
                      {ev.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600, color: '#334155' }}>{ev.activity_type}</td>
                  <td style={{ color: '#1e293b' }}>{ev.location_name}</td>
                  <td style={{ fontFamily: 'JetBrains Mono', fontSize: '0.8rem' }}>{ev.end_odometer} mi</td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>{ev.notes}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
