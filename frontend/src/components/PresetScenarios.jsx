import React from 'react';
import { PRESET_SCENARIOS } from '../utils/constants';
import { Zap } from 'lucide-react';

export default function PresetScenarios({ onSelectPreset }) {
  return (
    <div className="preset-section">
      <div className="preset-title" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <Zap size={14} color="#d97706" />
        <span>Quick Test Presets</span>
      </div>
      <div className="preset-grid">
        {PRESET_SCENARIOS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            className="preset-btn"
            onClick={() => onSelectPreset(preset)}
            title={preset.desc}
          >
            <span>{preset.title}</span>
            <span className="preset-tag">{preset.tag}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
