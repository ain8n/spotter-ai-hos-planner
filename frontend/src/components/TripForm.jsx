import React, { useState, useEffect, useRef } from 'react';
import { MapPin, ArrowRight, Truck, ChevronDown, ChevronUp, LocateFixed, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { searchLocations } from '../api/tripApi';

function LocationInput({
  label,
  value,
  onChange,
  onSelectCoords,
  placeholder,
  error,
  icon: Icon,
  allowGps = false,
  onUseGps,
  isGpsLoading = false,
  isGpsActive = false,
}) {
  const [query, setQuery] = useState(value || '');
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const wrapperRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    setQuery(value || '');
  }, [value]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    const text = e.target.value;
    setQuery(text);
    onChange(text);

    if (timerRef.current) clearTimeout(timerRef.current);

    // If the input is empty or "Your Location", do NOT search OSM
    if (!text || text.trim().length < 2 || text.trim().toLowerCase() === 'your location') {
      setSuggestions([]);
      setIsOpen(false);
      setHasSearched(false);
      return;
    }

    setIsLoading(true);
    setHasSearched(false);
    timerRef.current = setTimeout(async () => {
      try {
        const results = await searchLocations(text);
        setSuggestions(results || []);
        setIsOpen(true);
        setHasSearched(true);
      } catch (err) {
        setSuggestions([]);
        setIsOpen(true);
        setHasSearched(true);
      } finally {
        setIsLoading(false);
      }
    }, 280);
  };

  const handleSelectSuggestion = (item) => {
    const chosenName = item.name || item.display_name;
    setQuery(chosenName);
    onChange(chosenName);
    if (onSelectCoords) {
      onSelectCoords({
        lat: item.lat,
        lng: item.lng,
        name: chosenName,
        source: 'manual',
      });
    }
    setIsOpen(false);
    setSuggestions([]);
  };

  return (
    <div className="input-group" ref={wrapperRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label className="input-label" style={{ marginBottom: '0.35rem' }}>
          <Icon size={15} color="#2563eb" />
          <span>{label}</span>
        </label>
        {allowGps && isGpsActive && (
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              color: '#059669',
              background: '#ecfdf5',
              padding: '2px 6px',
              borderRadius: '4px',
              border: '1px solid #a7f3d0',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '3px',
              marginBottom: '0.35rem',
            }}
          >
            <CheckCircle2 size={11} color="#059669" />
            <span>GPS Active</span>
          </span>
        )}
      </div>

      <div className="input-field-wrapper" style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
        <input
          type="text"
          className={`input-field ${error ? 'error' : ''} ${allowGps && isGpsActive ? 'gps-active-field' : ''}`}
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (suggestions.length > 0 || hasSearched) setIsOpen(true);
          }}
          autoComplete="off"
        />

        {allowGps && (
          <button
            type="button"
            className="btn-gps-locate"
            onClick={onUseGps}
            disabled={isGpsLoading}
            title="Use Device GPS Location"
          >
            {isGpsLoading ? <Loader2 size={13} className="spin" /> : <LocateFixed size={13} />}
            <span>GPS</span>
          </button>
        )}

        {isLoading && !allowGps && (
          <span style={{ position: 'absolute', right: '12px', top: '13px', color: '#94a3b8' }}>
            <Loader2 size={15} className="spin" />
          </span>
        )}
      </div>

      {error && <span className="field-error-msg">{error}</span>}

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div className="location-autocomplete-list">
          {isLoading ? (
            <div className="autocomplete-empty-state">
              <Loader2 size={14} className="spin" />
              <span>Searching locations…</span>
            </div>
          ) : suggestions.length > 0 ? (
            suggestions.map((item, idx) => {
              const primaryName = item.name || item.display_name.split(',')[0];
              const secondaryName = item.display_name && item.display_name !== primaryName
                ? item.display_name
                : `${item.lat.toFixed(4)}, ${item.lng.toFixed(4)}`;

              return (
                <div
                  key={idx}
                  className="location-autocomplete-item"
                  onClick={() => handleSelectSuggestion(item)}
                >
                  <MapPin size={16} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="autocomplete-primary-name">{primaryName}</div>
                    <div className="autocomplete-secondary-name">{secondaryName}</div>
                  </div>
                </div>
              );
            })
          ) : (
            hasSearched && (
              <div className="autocomplete-empty-state">
                <AlertCircle size={14} color="#64748b" />
                <span>No exact location found. Try a nearby road, area, or city.</span>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

export default function TripForm({
  formData,
  coordsData = {},
  errors = {},
  isLoading,
  onChange,
  onCoordsChange,
  onSubmit,
  headerDetails,
  onHeaderChange,
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);

  const cycleUsed = parseFloat(formData.current_cycle_used_hrs || 0);
  const cycleRemaining = Math.max(0, 70.0 - cycleUsed).toFixed(1);

  const isGpsActive =
    (coordsData?.current?.source === 'gps' || formData.current_location === 'Your Location') &&
    coordsData?.current?.lat != null &&
    coordsData?.current?.lng != null;

  const handleUseCurrentGps = () => {
    if (!('geolocation' in navigator)) {
      alert('Geolocation is not supported on this device/browser.');
      return;
    }

    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude, accuracy } = pos.coords;
        // Strictly use "Your Location" - GPS coordinates are the source of truth!
        onChange('current_location', 'Your Location');
        if (onCoordsChange) {
          onCoordsChange('current', {
            lat: latitude,
            lng: longitude,
            name: 'Your Location',
            source: 'gps',
            accuracy: accuracy,
          });
        }
        setGpsLoading(false);
      },
      (err) => {
        setGpsLoading(false);
        alert('Unable to retrieve GPS location. Please check device location permissions or enter your location manually.');
      },
      { timeout: 10000, enableHighAccuracy: true, maximumAge: 0 }
    );
  };

  return (
    <section className="planner-card">
      <div className="planner-header">
        <h2>Plan Your Trip</h2>
        <p>
          Enter your current location, pickup, and drop-off destinations. The system will schedule compliant driving windows, mandatory breaks, fuel stops, and rest periods under FMCSA rules.
        </p>
      </div>

      <form onSubmit={onSubmit}>
        {/* 3 Main Location Inputs */}
        <div className="input-grid">
          <LocationInput
            label="Current Location"
            placeholder="Your Location or e.g. Richmond, VA"
            value={formData.current_location}
            onChange={(val) => {
              onChange('current_location', val);
              // If user manually clears or types a custom location, mark source as manual until a suggestion is picked
              if (onCoordsChange && val !== 'Your Location') {
                onCoordsChange('current', null);
              }
            }}
            onSelectCoords={(coords) => onCoordsChange && onCoordsChange('current', coords)}
            error={errors.current_location}
            icon={MapPin}
            allowGps={true}
            onUseGps={handleUseCurrentGps}
            isGpsLoading={gpsLoading}
            isGpsActive={isGpsActive}
          />

          <LocationInput
            label="Pickup Location"
            placeholder="e.g. Islamabad or Gary, IN"
            value={formData.pickup_location}
            onChange={(val) => {
              onChange('pickup_location', val);
              if (onCoordsChange) onCoordsChange('pickup', null);
            }}
            onSelectCoords={(coords) => onCoordsChange && onCoordsChange('pickup', coords)}
            error={errors.pickup_location}
            icon={Truck}
          />

          <LocationInput
            label="Drop-off Location"
            placeholder="e.g. Lahore or Newark, NJ"
            value={formData.dropoff_location}
            onChange={(val) => {
              onChange('dropoff_location', val);
              if (onCoordsChange) onCoordsChange('dropoff', null);
            }}
            onSelectCoords={(coords) => onCoordsChange && onCoordsChange('dropoff', coords)}
            error={errors.dropoff_location}
            icon={ArrowRight}
          />
        </div>

        {/* 70-Hour / 8-Day Cycle Hours Slider */}
        <div className="cycle-section">
          <div className="cycle-meta-row">
            <div className="cycle-label-group">
              <span className="cycle-title">Current 8-Day Cycle Used</span>
              <span className="cycle-subtitle">Hours already worked in your current 70-hour / 8-day rolling window</span>
            </div>
            <div className="cycle-indicator-pill">
              <span>{cycleUsed.toFixed(1)} hrs used</span>
              <span style={{ color: '#64748b', fontSize: '0.8rem' }}>&bull;</span>
              <span style={{ color: '#16a34a' }}>{cycleRemaining}h remaining</span>
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="70"
            step="0.5"
            value={cycleUsed}
            onChange={(e) => onChange('current_cycle_used_hrs', parseFloat(e.target.value))}
            className="cycle-range-input"
          />
        </div>

        {/* Optional Carrier & Driver Details Accordion */}
        <div style={{ marginBottom: '1.25rem' }}>
          <button
            type="button"
            className="btn-link-settings"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            <span>Carrier &amp; Driver Details (Optional)</span>
          </button>

          {showAdvanced && (
            <div className="advanced-fields-box">
              <div className="advanced-grid">
                <div>
                  <label className="input-label">Driver Name</label>
                  <input
                    type="text"
                    className="input-field"
                    value={headerDetails.driver_name}
                    onChange={(e) => onHeaderChange('driver_name', e.target.value)}
                  />
                </div>
                <div>
                  <label className="input-label">Carrier Name</label>
                  <input
                    type="text"
                    className="input-field"
                    value={headerDetails.carrier_name}
                    onChange={(e) => onHeaderChange('carrier_name', e.target.value)}
                  />
                </div>
                <div>
                  <label className="input-label">Truck / Tractor #</label>
                  <input
                    type="text"
                    className="input-field"
                    value={headerDetails.truck_tractor_num}
                    onChange={(e) => onHeaderChange('truck_tractor_num', e.target.value)}
                  />
                </div>
                <div>
                  <label className="input-label">Trailer #</label>
                  <input
                    type="text"
                    className="input-field"
                    value={headerDetails.trailer_num}
                    onChange={(e) => onHeaderChange('trailer_num', e.target.value)}
                  />
                </div>
                <div>
                  <label className="input-label">Main Office Address</label>
                  <input
                    type="text"
                    className="input-field"
                    value={headerDetails.main_office_address}
                    onChange={(e) => onHeaderChange('main_office_address', e.target.value)}
                  />
                </div>
                <div>
                  <label className="input-label">Home Terminal Address</label>
                  <input
                    type="text"
                    className="input-field"
                    value={headerDetails.home_terminal_address}
                    onChange={(e) => onHeaderChange('home_terminal_address', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Form Action Button */}
        <div className="form-action-bar">
          <button
            type="submit"
            className="btn-primary-plan"
            disabled={isLoading || gpsLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin" />
                <span>Planning…</span>
              </>
            ) : (
              <span>Plan Trip</span>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
