import React from 'react';
import { Truck } from 'lucide-react';

export default function Header() {
  return (
    <header className="app-navbar">
      <div className="navbar-container">
        <div className="brand">
          <div className="brand-icon">
            <Truck size={18} />
          </div>
          <div className="brand-text-block">
            <div className="brand-title">FMCSA Trip &amp; Daily Log Planner</div>
            <div className="brand-subtitle">Property-Carrying Commercial Motor Vehicle • 70-Hour / 8-Day HOS</div>
            <div className="compliance-tag mobile-compliance-tag">
              <span>49 CFR § 395 Compliant</span>
            </div>
          </div>
        </div>

        <div className="compliance-tag desktop-compliance-tag">
          <span>49 CFR § 395 Compliant</span>
        </div>
      </div>
    </header>
  );
}
