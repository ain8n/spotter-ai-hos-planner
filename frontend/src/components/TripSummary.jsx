import React from 'react';
import { Route, Clock, Calendar, Coffee, Fuel, Bed, RotateCcw, ArrowRight } from 'lucide-react';
import { formatHours, formatMiles } from '../utils/formatters';

export default function TripSummary({ summary, logsCount = 1, onGoToLogs }) {
  if (!summary) return null;

  return (
    <div>
      {/* 4 Key Answer Cards */}
      <div className="overview-answers-grid">
        <div className="answer-card">
          <div className="answer-card-label">
            <Route size={14} color="#2563eb" /> Total Distance
          </div>
          <div className="answer-card-val">{formatMiles(summary.total_distance_miles)}</div>
          <div className="answer-card-sub">Commercial highway routing</div>
        </div>

        <div className="answer-card">
          <div className="answer-card-label">
            <Clock size={14} color="#059669" /> Driving Time
          </div>
          <div className="answer-card-val">{formatHours(summary.total_driving_hours)}</div>
          <div className="answer-card-sub">{summary.total_on_duty_hours}h total on-duty work</div>
        </div>

        <div className="answer-card">
          <div className="answer-card-label">
            <Clock size={14} color="#7c3aed" /> Total Trip Time
          </div>
          <div className="answer-card-val">{formatHours(summary.total_trip_duration_hours)}</div>
          <div className="answer-card-sub">Including all rests, breaks &amp; loads</div>
        </div>

        <div className="answer-card">
          <div className="answer-card-label">
            <Calendar size={14} color="#ea580c" /> Daily ELD Sheets
          </div>
          <div className="answer-card-val">{logsCount} {logsCount === 1 ? 'Day' : 'Days'}</div>
          <div className="answer-card-sub">Form 395 24h calendar logs</div>
        </div>
      </div>

      {/* Compliance & Stops Summary Row */}
      <div className="compliance-summary-card">
        <div>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.2rem' }}>
            Required Stops &amp; Rest Schedule
          </div>
          <div className="stops-counter-bar">
            <div className="stop-count-item">
              <Coffee size={15} color="#0284c7" />
              <span>{summary.rest_breaks_30m_count} &times; 30m Break</span>
            </div>
            <div className="stop-count-item">
              <Fuel size={15} color="#d97706" />
              <span>{summary.fuel_stops_count} &times; Fuel Stop (&le;1,000 mi)</span>
            </div>
            <div className="stop-count-item">
              <Bed size={15} color="#475569" />
              <span>{summary.daily_rests_10h_count} &times; 10h Overnight Rest</span>
            </div>
            {summary.restarts_34h_count > 0 && (
              <div className="stop-count-item" style={{ color: '#be185d' }}>
                <RotateCcw size={15} color="#db2777" />
                <span>{summary.restarts_34h_count} &times; 34h Restart (Cycle Reset)</span>
              </div>
            )}
          </div>
        </div>

        <div>
          <button
            type="button"
            className="btn-log-action"
            style={{ background: '#2563eb', color: '#ffffff', borderColor: '#2563eb' }}
            onClick={onGoToLogs}
          >
            <span>View Daily Logs</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
