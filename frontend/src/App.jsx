import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import TripForm from './components/TripForm';
import LoadingIndicator from './components/LoadingIndicator';
import TripSummary from './components/TripSummary';
import MapView from './components/MapView';
import DailyLogViewer from './components/DailyLogViewer';
import RouteDirections from './components/RouteDirections';
import { planTrip } from './api/tripApi';
import { DEFAULT_LOG_HEADER } from './utils/constants';
import { getTimezoneFromCoordinates } from './utils/timezone';
import {
  Map,
  LayoutDashboard,
  FileText,
  ListOrdered,
  AlertCircle,
  Info,
  Loader2,
  Edit3,
} from 'lucide-react';

export default function App() {
  const [formData, setFormData] = useState({
    current_location: 'Your Location',
    pickup_location: 'Richmond, VA',
    dropoff_location: 'Newark, NJ',
    current_cycle_used_hrs: 12.0,
  });

  const [coordsData, setCoordsData] = useState({
    current: null,
    pickup: null,
    dropoff: null,
  });

  const [timeZone, setTimeZone] = useState('America/New_York');
  const [headerDetails, setHeaderDetails] = useState(DEFAULT_LOG_HEADER);
  // Default to Trip on initial load so user can enter details and press Plan Trip
  const [activeTab, setActiveTab] = useState('trip');
  const [isLoading, setIsLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [locationNotice, setLocationNotice] = useState(null);
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState(null);
  const [planResult, setPlanResult] = useState(null);

  // Startup: Acquire exact GPS current location ONLY without automatically planning trip
  useEffect(() => {
    acquireInitialLocation();
  }, []);

  const acquireInitialLocation = () => {
    if (!('geolocation' in navigator)) {
      setFormData((prev) => ({
        ...prev,
        current_location: prev.current_location || 'Richmond, VA',
      }));
      const fallbackTz = getTimezoneFromCoordinates(37.5407, -77.4360);
      setTimeZone(fallbackTz);
      setCoordsData((prev) => ({
        ...prev,
        current: prev.current || { lat: 37.5407, lng: -77.4360, name: 'Richmond, VA', source: 'manual', timezone: fallbackTz },
      }));
      return;
    }

    setIsLocating(true);
    setLocationNotice(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude, accuracy } = pos.coords;
        const tz = getTimezoneFromCoordinates(latitude, longitude);
        setTimeZone(tz);
        const gpsCoords = {
          lat: latitude,
          lng: longitude,
          name: 'Your Location',
          source: 'gps',
          accuracy: accuracy,
          timezone: tz,
        };

        // Populate Current Location with GPS coordinates and display "Your Location"
        setFormData((prev) => {
          // If user has already entered a manual location, preserve it
          if (prev.current_location && prev.current_location !== 'Your Location' && prev.current_location !== 'Richmond, VA') {
            return prev;
          }
          return {
            ...prev,
            current_location: 'Your Location',
          };
        });

        setCoordsData((prev) => {
          if (prev.current && prev.current.source === 'manual') {
            return prev;
          }
          return {
            ...prev,
            current: gpsCoords,
          };
        });

        setIsLocating(false);
        // CRITICAL: DO NOT CALL PLAN TRIP AUTOMATICALLY! WAIT FOR EXPLICIT USER ACTION.
      },
      (err) => {
        setIsLocating(false);
        if (err.code === 1) {
          setLocationNotice('Location access was denied. You can enter your current location manually in the Trip form.');
        } else {
          setLocationNotice('Unable to acquire GPS position. You can enter your current location manually in the Trip form.');
        }
        const fallbackTz = getTimezoneFromCoordinates(37.5407, -77.4360);
        setTimeZone(fallbackTz);
        setFormData((prev) => ({
          ...prev,
          current_location: prev.current_location || 'Richmond, VA',
        }));
        setCoordsData((prev) => ({
          ...prev,
          current: prev.current || { lat: 37.5407, lng: -77.4360, name: 'Richmond, VA', source: 'manual', timezone: fallbackTz },
        }));
        // CRITICAL: DO NOT CALL PLAN TRIP AUTOMATICALLY! WAIT FOR EXPLICIT USER ACTION.
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
  };

  const executePlanTrip = async (tripData, headerData, customCoords) => {
    setIsLoading(true);
    setErrors({});
    setGlobalError(null);

    try {
      const currentCoords = customCoords?.current || coordsData?.current;
      const effectiveTz = (currentCoords && currentCoords.lat != null && currentCoords.lng != null)
        ? (currentCoords.timezone || getTimezoneFromCoordinates(currentCoords.lat, currentCoords.lng))
        : timeZone;

      const payload = {
        current_location: tripData.current_location || 'Your Location',
        pickup_location: tripData.pickup_location || 'Richmond, VA',
        dropoff_location: tripData.dropoff_location || 'Newark, NJ',
        current_cycle_used_hrs: parseFloat(tripData.current_cycle_used_hrs) || 0.0,
        coordinates: customCoords || {},
        options: {
          start_datetime: new Date().toISOString(),
          header: headerData,
          coordinates: customCoords || {},
          timezone: effectiveTz,
        },
      };

      const result = await planTrip(payload);
      if (result?.summary?.timezone || result?.timezone) {
        setTimeZone(result.summary?.timezone || result.timezone);
      }
      setPlanResult(result);
      // On successful plan, switch to Map tab to display the calculated route
      setActiveTab('map');
      setTimeout(() => window.dispatchEvent(new Event('resize')), 150);
    } catch (err) {
      if (err.fields && Object.keys(err.fields).length > 0) {
        setErrors(err.fields);
      } else {
        setGlobalError(err.message || 'Unable to plan trip. Please check your locations and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const handleCoordsChange = (pointType, coords) => {
    setCoordsData((prev) => ({ ...prev, [pointType]: coords }));
    if (pointType === 'current' && coords && coords.lat != null && coords.lng != null) {
      const tz = coords.timezone || getTimezoneFromCoordinates(coords.lat, coords.lng);
      setTimeZone(tz);
    }
  };

  const handleHeaderChange = (field, value) => {
    setHeaderDetails((prev) => ({ ...prev, [field]: value }));
  };

  const handleFormSubmit = (e) => {
    if (e) e.preventDefault();
    executePlanTrip(formData, headerDetails, coordsData);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    const pageEl = document.querySelector('.page-container');
    if (pageEl) pageEl.scrollTop = 0;
    if (tab === 'map') {
      setTimeout(() => window.dispatchEvent(new Event('resize')), 150);
    }
  };

  // Ensure any screen/tab change always starts at the top
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    const pageEl = document.querySelector('.page-container');
    if (pageEl) pageEl.scrollTop = 0;
  }, [activeTab]);

  return (
    <div className="app-root-container">
      {/* Top Navbar Header */}
      <Header />

      <main className="page-container">
        {/* Startup Location Status Notification */}
        {isLocating && (
          <div className="startup-locating-banner">
            <Loader2 size={16} className="spin" color="#2563eb" />
            <span>Acquiring exact GPS location…</span>
          </div>
        )}

        {locationNotice && !isLocating && (
          <div className="info-notice-banner" style={{ background: '#fffbeb', borderLeftColor: '#d97706', marginBottom: '1rem' }}>
            <Info size={16} color="#d97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            <p style={{ color: '#92400e', fontSize: '0.82rem' }}>{locationNotice}</p>
          </div>
        )}

        {/* Global Error Banner */}
        {globalError && (
          <div className="info-notice-banner error-banner">
            <AlertCircle size={20} color="#dc2626" style={{ flexShrink: 0 }} />
            <div>
              <p style={{ color: '#991b1b', fontWeight: 700 }}>Unable to calculate route</p>
              <p style={{ color: '#b91c1c', fontSize: '0.85rem' }}>{globalError}</p>
            </div>
          </div>
        )}

        {/* Loading Indicator ("Planning…") */}
        {isLoading && <LoadingIndicator />}

        {/* Established Desktop Navigation Tabs */}
        <div className="main-tabs-nav desktop-tabs-only">
          <button
            type="button"
            className={`main-tab ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => handleTabChange('map')}
          >
            <Map size={18} />
            <span>Map</span>
            {planResult?.stops?.length > 0 && (
              <span className="tab-badge">{planResult.stops.length}</span>
            )}
          </button>

          <button
            type="button"
            className={`main-tab ${activeTab === 'trip' ? 'active' : ''}`}
            onClick={() => handleTabChange('trip')}
          >
            <LayoutDashboard size={18} />
            <span>Trip</span>
          </button>

          <button
            type="button"
            className={`main-tab ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => handleTabChange('logs')}
          >
            <FileText size={18} />
            <span>Logs</span>
            {planResult?.logs?.length > 0 && (
              <span className="tab-badge">{planResult.logs.length}</span>
            )}
          </button>

          <button
            type="button"
            className={`main-tab ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => handleTabChange('details')}
          >
            <ListOrdered size={18} />
            <span>Details</span>
          </button>
        </div>

        {/* Mobile Trip Status & Quick Edit Bar (Visible on mobile when planResult exists) */}
        {planResult && (
          <div className="mobile-trip-status-bar">
            <div className="mobile-status-info">
              <span className="mobile-route-pill">
                {formData.current_location === 'Your Location' ? 'Your Location' : formData.current_location.split(',')[0]} &rarr; {formData.dropoff_location.split(',')[0]}
              </span>
              <span className="mobile-route-meta">
                {planResult.summary?.total_distance_miles || 0} mi &bull; {planResult.logs?.length || 1} {planResult.logs?.length === 1 ? 'Day' : 'Days'}
              </span>
            </div>
            <button
              type="button"
              className="btn-mobile-edit-trip"
              onClick={() => handleTabChange('trip')}
              aria-label="Edit Trip"
            >
              <Edit3 size={14} />
              <span>Edit</span>
            </button>
          </div>
        )}

        {/* Tab 1: Map Screen */}
        <div className={`tab-content-panel ${activeTab === 'map' ? 'tab-visible' : 'tab-hidden'}`}>
          {planResult && (
            <div className="desktop-summary-strip" style={{ marginBottom: '1rem' }}>
              <TripSummary
                summary={planResult.summary}
                logsCount={planResult.logs?.length || 1}
                onGoToLogs={() => handleTabChange('logs')}
              />
            </div>
          )}
          {planResult ? (
            <MapView
              routeData={planResult.route}
              stops={planResult.stops}
              timeline={planResult.timeline}
              timezone={planResult.summary?.timezone || planResult.timezone || timeZone}
            />
          ) : (
            <div className="planner-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
              <Map size={36} color="#94a3b8" style={{ margin: '0 auto 1rem', display: 'block' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>No Active Trip Planned</h3>
              <p style={{ color: '#64748b', fontSize: '0.88rem', maxWidth: '440px', margin: '0 auto 1.25rem' }}>
                Enter your trip destinations and 8-day cycle hours in the <strong>Trip</strong> tab, then press <strong>Plan Trip</strong> to calculate your route and view stops on the map.
              </p>
              <button
                type="button"
                className="btn-primary-plan"
                style={{ width: 'auto', padding: '0.65rem 1.5rem', display: 'inline-flex', margin: '0 auto' }}
                onClick={() => handleTabChange('trip')}
              >
                Go to Trip Form
              </button>
            </div>
          )}
        </div>

        {/* Tab 2: Trip Planning Screen */}
        <div className={`tab-content-panel ${activeTab === 'trip' ? 'tab-visible' : 'tab-hidden'}`}>
          <TripForm
            formData={formData}
            coordsData={coordsData}
            errors={errors}
            isLoading={isLoading}
            onChange={handleFormChange}
            onCoordsChange={handleCoordsChange}
            onSubmit={handleFormSubmit}
            headerDetails={headerDetails}
            onHeaderChange={handleHeaderChange}
          />
        </div>

        {/* Tab 3: Daily Logs Screen */}
        <div className={`tab-content-panel ${activeTab === 'logs' ? 'tab-visible' : 'tab-hidden'}`}>
          {planResult?.logs?.length > 0 ? (
            <DailyLogViewer logs={planResult.logs} />
          ) : (
            <div className="planner-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
              <FileText size={36} color="#94a3b8" style={{ margin: '0 auto 1rem', display: 'block' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>No Daily Logs Generated Yet</h3>
              <p style={{ color: '#64748b', fontSize: '0.88rem', maxWidth: '440px', margin: '0 auto 1.25rem' }}>
                Fill out the trip form in the <strong>Trip</strong> tab and click <strong>Plan Trip</strong> to automatically generate your 24-hour FMCSA Driver&apos;s Daily Log sheets.
              </p>
              <button
                type="button"
                className="btn-primary-plan"
                style={{ width: 'auto', padding: '0.65rem 1.5rem', display: 'inline-flex', margin: '0 auto' }}
                onClick={() => handleTabChange('trip')}
              >
                Go to Trip Form
              </button>
            </div>
          )}
        </div>

        {/* Tab 4: Details / Directions & Events Screen */}
        <div className={`tab-content-panel ${activeTab === 'details' ? 'tab-visible' : 'tab-hidden'}`}>
          {planResult ? (
            <>
              <div style={{ marginBottom: '1.25rem' }}>
                <TripSummary
                  summary={planResult.summary}
                  logsCount={planResult.logs?.length || 1}
                  onGoToLogs={() => handleTabChange('logs')}
                />
              </div>
              <RouteDirections
                instructions={planResult.instructions}
                stops={planResult.stops}
                timeline={planResult.timeline}
                timezone={planResult.summary?.timezone || planResult.timezone || timeZone}
              />
            </>
          ) : (
            <div className="planner-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
              <ListOrdered size={36} color="#94a3b8" style={{ margin: '0 auto 1rem', display: 'block' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>No Turn-by-Turn Directions Available</h3>
              <p style={{ color: '#64748b', fontSize: '0.88rem', maxWidth: '440px', margin: '0 auto 1.25rem' }}>
                Plan a trip in the <strong>Trip</strong> tab to view leg directions, turn-by-turn guidance, and the complete chronological duty status event log.
              </p>
              <button
                type="button"
                className="btn-primary-plan"
                style={{ width: 'auto', padding: '0.65rem 1.5rem', display: 'inline-flex', margin: '0 auto' }}
                onClick={() => handleTabChange('trip')}
              >
                Go to Trip Form
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Established Mobile Android Bottom Navigation Bar (max-width: 768px) */}
      <nav className="mobile-bottom-nav-bar">
        <button
          type="button"
          className={`mobile-nav-item ${activeTab === 'map' ? 'nav-active' : ''}`}
          onClick={() => handleTabChange('map')}
        >
          <Map size={22} />
          <span>Map</span>
        </button>

        <button
          type="button"
          className={`mobile-nav-item ${activeTab === 'trip' ? 'nav-active' : ''}`}
          onClick={() => handleTabChange('trip')}
        >
          <LayoutDashboard size={22} />
          <span>Trip</span>
        </button>

        <button
          type="button"
          className={`mobile-nav-item ${activeTab === 'logs' ? 'nav-active' : ''}`}
          onClick={() => handleTabChange('logs')}
        >
          <FileText size={22} />
          <span>Logs</span>
          {planResult?.logs?.length > 0 && (
            <span className="mobile-nav-badge">{planResult.logs.length}</span>
          )}
        </button>

        <button
          type="button"
          className={`mobile-nav-item ${activeTab === 'details' ? 'nav-active' : ''}`}
          onClick={() => handleTabChange('details')}
        >
          <ListOrdered size={22} />
          <span>Details</span>
        </button>
      </nav>
    </div>
  );
}
