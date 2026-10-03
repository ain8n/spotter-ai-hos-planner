import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { formatTimeOnly, formatHours, formatMiles } from '../utils/formatters';
import {
  Navigation,
  Navigation2,
  MapPin,
  Clock,
  LocateFixed,
  Maximize2,
  Minimize2,
  RotateCcw,
  Volume2,
  VolumeX,
  Layers,
  X,
} from 'lucide-react';

// Fix default Leaflet icon paths
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Helper: Calculate compass bearing between two coordinates
function calculateBearing(lat1, lon1, lat2, lon2) {
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const y = Math.sin(dLon) * Math.cos((lat2 * Math.PI) / 180);
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.cos(dLon);
  let brng = (Math.atan2(y, x) * 180) / Math.PI;
  return (brng + 360) % 360;
}

export default function MapView({ routeData, stops, timezone }) {
  const mapContainerRef = useRef(null);
  const mapWrapperRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});
  const leg1PolylineRef = useRef(null);
  const leg2PolylineRef = useRef(null);
  const userMarkerRef = useRef(null);
  const watchIdRef = useRef(null);

  // Live navigation state
  const [isNavigating, setIsNavigating] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isVoiceMuted, setIsVoiceMuted] = useState(false);
  const [showLegend, setShowLegend] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [userHeading, setUserHeading] = useState(0);
  const [hasRealHeading, setHasRealHeading] = useState(false);
  const [geoStatus, setGeoStatus] = useState('idle'); // 'idle' | 'locating' | 'granted' | 'denied' | 'unavailable'
  const [selectedStopIdx, setSelectedStopIdx] = useState(0);
  const [nextStop, setNextStop] = useState(null);
  const [currentManeuver, setCurrentManeuver] = useState(null);
  const [autoFollow, setAutoFollow] = useState(true);

  // Extract key locations
  const currentLoc = routeData?.locations?.current || null;
  const pickupLoc = routeData?.locations?.pickup || null;
  const dropoffLoc = routeData?.locations?.dropoff || null;

  // Determine next upcoming stop and first maneuver
  useEffect(() => {
    if (!stops || stops.length === 0) {
      setNextStop(null);
      return;
    }
    const target = stops.find((s) => s.stop_type !== 'START') || stops[0];
    setNextStop(target);

    // Initial maneuver step from leg1 or leg2
    const firstLeg = routeData?.leg1?.instructions || [];
    const secondLeg = routeData?.leg2?.instructions || [];
    const allSteps = [...firstLeg, ...secondLeg];
    if (allSteps.length > 0) {
      setCurrentManeuver(allSteps[0]);
    }
  }, [stops, routeData]);

  // Voice Speech Helper
  const speakInstruction = useCallback(
    (text) => {
      if (isVoiceMuted || !('speechSynthesis' in window)) return;
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.lang = 'en-US';
        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.warn('Speech synthesis error', e);
      }
    },
    [isVoiceMuted]
  );

  // Center on vehicle with forward-looking driving offset
  const centerOnVehicleWithOffset = useCallback((lat, lng, zoom = 16) => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;
    try {
      const offsetLat = lat + 0.0025; // Center slightly ahead of vehicle
      map.flyTo([offsetLat, lng], zoom, {
        duration: 0.8,
        easeLinearity: 0.25,
      });
    } catch (e) {}
  }, []);

  // Handle Geolocation Watch for Navigation
  const startLiveTracking = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setGeoStatus('unavailable');
      return;
    }

    setGeoStatus('locating');

    if (nextStop) {
      speakInstruction(`Starting navigation to ${nextStop.name}`);
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude, heading, speed, accuracy } = pos.coords;
        setGeoStatus('granted');
        setUserLocation({ lat: latitude, lng: longitude, accuracy });

        if (heading !== null && !isNaN(heading) && heading > 0) {
          setUserHeading(heading);
          setHasRealHeading(true);
        } else {
          setHasRealHeading(false);
        }

        centerOnVehicleWithOffset(latitude, longitude, 16);
      },
      (err) => {
        console.warn('Geolocation error:', err.message);
        if (err.code === 1) {
          setGeoStatus('denied');
        } else {
          setGeoStatus('unavailable');
        }
        if (currentLoc) {
          centerOnVehicleWithOffset(currentLoc.lat, currentLoc.lng, 16);
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
    );

    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, heading, speed, accuracy } = pos.coords;
        setGeoStatus('granted');
        setUserLocation({ lat: latitude, lng: longitude, accuracy });

        if (heading !== null && !isNaN(heading) && heading > 0) {
          setUserHeading(heading);
          setHasRealHeading(true);
        }
      },
      (err) => {
        console.warn('Watch position error:', err.message);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 2000 }
    );
  }, [nextStop, currentLoc, speakInstruction, centerOnVehicleWithOffset]);

  const stopLiveTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }, []);

  // Toggle navigation mode
  const handleToggleNavigation = () => {
    if (!isNavigating) {
      setIsNavigating(true);
      setAutoFollow(true);
      startLiveTracking();
      const loc = userLocation || (currentLoc ? { lat: currentLoc.lat, lng: currentLoc.lng } : null);
      if (loc) {
        centerOnVehicleWithOffset(loc.lat, loc.lng, 16);
      }
    } else {
      setIsNavigating(false);
      stopLiveTracking();
      fitRouteBounds();
    }
  };

  // Toggle voice mute (Mutes audio without stopping navigation!)
  const handleToggleVoice = () => {
    setIsVoiceMuted((prev) => {
      const next = !prev;
      if (!next && currentManeuver) {
        speakInstruction(currentManeuver.text);
      } else if (next && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      return next;
    });
  };

  // Toggle Fullscreen mode (Full 100vw × 100vh on Desktop and Mobile)
  const handleToggleFullscreen = () => {
    setIsFullscreen((prev) => {
      const next = !prev;
      if (next) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
      return next;
    });

    // Invalidate size immediately and after layout paint
    setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 50);

    setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 200);
  };

  // Recenter control restores navigation-follow view
  const handleRecenter = () => {
    setAutoFollow(true);
    const target = userLocation || (currentLoc ? { lat: currentLoc.lat, lng: currentLoc.lng } : null);
    if (target) {
      if (isNavigating) {
        centerOnVehicleWithOffset(target.lat, target.lng, 16);
      } else {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo([target.lat, target.lng], 15, { duration: 0.8 });
        }
      }
    }
  };

  // Fit bounds helper
  const fitRouteBounds = useCallback(() => {
    if (!mapInstanceRef.current) return;
    const allPts = [];

    const leg1Geo = routeData?.leg1?.geometry || [];
    const leg2Geo = routeData?.leg2?.geometry || [];

    [...leg1Geo, ...leg2Geo].forEach((pt) => {
      if (Array.isArray(pt) && pt.length >= 2 && !isNaN(pt[0]) && !isNaN(pt[1])) {
        allPts.push([pt[0], pt[1]]);
      }
    });

    if (stops && stops.length > 0) {
      stops.forEach((s) => {
        if (s.latitude && s.longitude) {
          allPts.push([s.latitude, s.longitude]);
        }
      });
    }

    if (allPts.length > 0) {
      try {
        const bounds = L.latLngBounds(allPts);
        mapInstanceRef.current.fitBounds(bounds, { padding: [45, 45], maxZoom: 13 });
      } catch (e) {}
    }
  }, [routeData, stops]);

  // Click itinerary stop to focus map
  const handleSelectItineraryStop = (idx, stop) => {
    setSelectedStopIdx(idx);
    if (!mapInstanceRef.current || !stop.latitude || !stop.longitude) return;

    try {
      mapInstanceRef.current.flyTo([stop.latitude, stop.longitude], 13, { duration: 0.8 });
      const marker = markersRef.current[idx];
      if (marker) {
        marker.openPopup();
      }
    } catch (e) {}
  };

  // Initialize Leaflet Map defensively
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      if (mapContainerRef.current._leaflet_id) {
        delete mapContainerRef.current._leaflet_id;
      }

      try {
        const map = L.map(mapContainerRef.current, {
          zoomControl: true,
          scrollWheelZoom: true,
          preferCanvas: true,
        }).setView([39.8283, -98.5795], 4);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors',
          maxZoom: 19,
        }).addTo(map);

        map.on('dragstart', () => {
          if (isNavigating) setAutoFollow(false);
        });
        map.on('zoomstart', () => {
          if (isNavigating) setAutoFollow(false);
        });

        mapInstanceRef.current = map;
      } catch (err) {
        console.error('Leaflet initialization error:', err);
      }
    }

    const map = mapInstanceRef.current;
    if (!map) return;

    // Clean up existing markers and polylines
    Object.values(markersRef.current).forEach((m) => {
      try {
        map.removeLayer(m);
      } catch (e) {}
    });
    markersRef.current = {};

    if (leg1PolylineRef.current) {
      try {
        map.removeLayer(leg1PolylineRef.current);
      } catch (e) {}
      leg1PolylineRef.current = null;
    }
    if (leg2PolylineRef.current) {
      try {
        map.removeLayer(leg2PolylineRef.current);
      } catch (e) {}
      leg2PolylineRef.current = null;
    }

    try {
      // 1. Draw Distinct Route Segments
      // Leg 1: Current Location -> Pickup (Approach Corridor: Teal #0d9488)
      const leg1Geo = routeData?.leg1?.geometry || [];
      if (leg1Geo.length > 0) {
        L.polyline(leg1Geo, {
          color: '#0f766e',
          weight: 7,
          opacity: 0.35,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(map);

        const poly1 = L.polyline(leg1Geo, {
          color: '#0d9488',
          weight: 4.5,
          opacity: 0.95,
          dashArray: '8, 8',
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(map);

        leg1PolylineRef.current = poly1;
      }

      // Leg 2: Pickup -> Drop-off (Primary Loaded Freight Route: Bold Royal Blue #2563eb)
      const leg2Geo = routeData?.leg2?.geometry || [];
      if (leg2Geo.length > 0) {
        L.polyline(leg2Geo, {
          color: '#1e3a8a',
          weight: 8,
          opacity: 0.35,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(map);

        const poly2 = L.polyline(leg2Geo, {
          color: '#2563eb',
          weight: 5.5,
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(map);

        leg2PolylineRef.current = poly2;
      }

      // 2. Render Clean Markers (No emoji logos; clean colored dots)
      if (stops && stops.length > 0) {
        // Detect if Start and Pickup are at the same or extremely close coordinates
        const startStop = stops.find((s) => s.stop_type === 'START');
        const pickupStop = stops.find((s) => s.stop_type === 'PICKUP');
        const isStartPickupCoincident = Boolean(
          startStop &&
          pickupStop &&
          startStop.latitude &&
          pickupStop.latitude &&
          Math.abs(startStop.latitude - pickupStop.latitude) < 0.0015 &&
          Math.abs(startStop.longitude - pickupStop.longitude) < 0.0015
        );

        stops.forEach((stop, idx) => {
          const { stop_type, latitude, longitude, name, arrival_time, departure_time, duration_hours, mile_marker, reason } = stop;
          if (!latitude || !longitude || isNaN(latitude) || isNaN(longitude)) return;

          let markerHtml = '';
          let zIndex = 600;
          let iconSize = [125, 26];
          let iconAnchor = [62, 13];
          let popupAnchor = [0, -15];

          if (stop_type === 'START') {
            zIndex = 1000;
            const startLabel = name === 'Your Location' || name.startsWith('Your Location') ? 'Your Location' : name.split(',')[0];
            if (isStartPickupCoincident) {
              // Offset visually above the coordinate point
              iconSize = [130, 26];
              iconAnchor = [65, 34];
              popupAnchor = [0, -36];
              markerHtml = `
                <div class="map-marker-pill start-pill pill-offset-top">
                  <span class="marker-dot dot-blue"></span>
                  <span class="marker-pill-text"><strong>Start:</strong> ${startLabel}</span>
                </div>
              `;
            } else {
              iconSize = [125, 26];
              iconAnchor = [62, 13];
              popupAnchor = [0, -15];
              markerHtml = `
                <div class="map-marker-pill start-pill">
                  <span class="marker-dot dot-blue"></span>
                  <span class="marker-pill-text"><strong>Start:</strong> ${startLabel}</span>
                </div>
              `;
            }
          } else if (stop_type === 'PICKUP') {
            zIndex = 950;
            const pickupLabel = name.split(',')[0];
            if (isStartPickupCoincident) {
              // Offset visually below the coordinate point
              iconSize = [130, 26];
              iconAnchor = [65, -6];
              popupAnchor = [0, 8];
              markerHtml = `
                <div class="map-marker-pill pickup-pill pill-offset-bottom">
                  <span class="marker-dot dot-green"></span>
                  <span class="marker-pill-text"><strong>Pickup:</strong> ${pickupLabel}</span>
                </div>
              `;
            } else {
              iconSize = [125, 26];
              iconAnchor = [62, 13];
              popupAnchor = [0, -15];
              markerHtml = `
                <div class="map-marker-pill pickup-pill">
                  <span class="marker-dot dot-green"></span>
                  <span class="marker-pill-text"><strong>Pickup:</strong> ${pickupLabel}</span>
                </div>
              `;
            }
          } else if (stop_type === 'DROPOFF') {
            zIndex = 980;
            iconSize = [130, 26];
            iconAnchor = [65, 13];
            popupAnchor = [0, -15];
            const dropoffLabel = name.split(',')[0];
            markerHtml = `
              <div class="map-marker-pill dropoff-pill">
                <span class="marker-dot dot-red"></span>
                <span class="marker-pill-text"><strong>Drop-off:</strong> ${dropoffLabel}</span>
              </div>
            `;
          } else if (stop_type === 'FUEL') {
            zIndex = 750;
            iconSize = [18, 18];
            iconAnchor = [9, 9];
            popupAnchor = [0, -10];
            markerHtml = `<div class="stop-dot-marker dot-amber" title="Fuel Stop (≤1,000 mi)"></div>`;
          } else if (stop_type === 'REST_30') {
            zIndex = 700;
            iconSize = [18, 18];
            iconAnchor = [9, 9];
            popupAnchor = [0, -10];
            markerHtml = `<div class="stop-dot-marker dot-sky" title="30-Min Rest Break"></div>`;
          } else if (stop_type === 'REST_10') {
            zIndex = 800;
            iconSize = [18, 18];
            iconAnchor = [9, 9];
            popupAnchor = [0, -10];
            markerHtml = `<div class="stop-dot-marker dot-slate" title="10-Hour Overnight Rest"></div>`;
          } else if (stop_type === 'RESTART_34') {
            zIndex = 850;
            iconSize = [18, 18];
            iconAnchor = [9, 9];
            popupAnchor = [0, -10];
            markerHtml = `<div class="stop-dot-marker dot-pink" title="34-Hour Restart"></div>`;
          }

          const divIcon = L.divIcon({
            className: 'clean-leaflet-marker',
            html: markerHtml,
            iconSize: iconSize,
            iconAnchor: iconAnchor,
            popupAnchor: popupAnchor,
          });

          const stopLabel = stop_type.replace('_', ' ');
          const displayStopName = (stop_type === 'START' && (name === 'Your Location' || name.startsWith('Your Location')))
            ? 'Your Location (Device GPS Position)'
            : name;
          const popupContent = `
            <div class="marker-popup-card">
              <div class="popup-header-row">
                <span class="popup-type-tag ${stop_type.toLowerCase()}">${stopLabel}</span>
                <span class="popup-mile">Mile ${mile_marker} mi</span>
              </div>
              <div class="popup-stop-name">${displayStopName}</div>
              <div class="popup-details-grid">
                <div><strong>Arrive:</strong> ${formatTimeOnly(arrival_time, timezone)}</div>
                <div><strong>Depart:</strong> ${formatTimeOnly(departure_time, timezone)}</div>
                <div><strong>Duration:</strong> ${formatHours(duration_hours)}</div>
              </div>
              <div class="popup-reason-box"><em>${reason}</em></div>
            </div>
          `;

          const m = L.marker([latitude, longitude], { icon: divIcon, zIndexOffset: zIndex })
            .bindPopup(popupContent)
            .addTo(map);

          m.on('click', () => {
            setSelectedStopIdx(idx);
          });

          markersRef.current[idx] = m;
        });
      }

      if (!isNavigating) {
        fitRouteBounds();
      }
    } catch (renderErr) {
      console.warn('Map polyline/marker render error:', renderErr);
    }

    const resizeTimer = setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    }, 200);

    return () => {
      clearTimeout(resizeTimer);
    };
  }, [routeData, stops, isNavigating, fitRouteBounds]);

  // Update Live User Vehicle Marker
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    const loc = userLocation || (currentLoc ? { lat: currentLoc.lat, lng: currentLoc.lng } : null);

    if (loc && loc.lat && loc.lng) {
      try {
        if (!userMarkerRef.current) {
          const userDiv = L.divIcon({
            className: 'user-nav-vehicle-marker',
            html: `
              <div class="nav-vehicle-container ${isNavigating ? 'active-nav' : ''}">
                <div class="nav-radar-wave"></div>
                <div class="nav-arrow-disk" style="transform: rotate(${hasRealHeading ? userHeading : 0}deg);">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="#ffffff">
                    <polygon points="12 2 20 21 12 17 4 21 12 2" />
                  </svg>
                </div>
              </div>
            `,
            iconSize: [38, 38],
            iconAnchor: [19, 19],
          });

          userMarkerRef.current = L.marker([loc.lat, loc.lng], {
            icon: userDiv,
            zIndexOffset: 2000,
          }).addTo(map);
        } else {
          userMarkerRef.current.setLatLng([loc.lat, loc.lng]);
          const el = userMarkerRef.current.getElement();
          if (el) {
            const arrow = el.querySelector('.nav-arrow-disk');
            if (arrow) {
              arrow.style.transform = `rotate(${hasRealHeading ? userHeading : 0}deg)`;
            }
            const container = el.querySelector('.nav-vehicle-container');
            if (container) {
              if (isNavigating) container.classList.add('active-nav');
              else container.classList.remove('active-nav');
            }
          }
        }

        if (isNavigating && autoFollow) {
          centerOnVehicleWithOffset(loc.lat, loc.lng, 16);
        }
      } catch (e) {}
    }
  }, [userLocation, userHeading, hasRealHeading, isNavigating, autoFollow, currentLoc, centerOnVehicleWithOffset]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopLiveTracking();
      document.body.style.overflow = '';
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {}
        mapInstanceRef.current = null;
      }
      if (mapContainerRef.current && mapContainerRef.current._leaflet_id) {
        delete mapContainerRef.current._leaflet_id;
      }
    };
  }, [stopLiveTracking]);

  return (
    <div
      ref={mapWrapperRef}
      className={`nav-experience-wrapper ${isFullscreen ? 'map-fullscreen-viewport' : ''}`}
    >
      <div className="route-layout-grid">
        {/* Left Column: Itinerary (Preserved on Desktop, Hidden in Fullscreen mode) */}
        {!isFullscreen && (
          <div className="itinerary-container">
            <div className="itinerary-title">
              <Clock size={17} color="#2563eb" />
              <span>Trip Itinerary</span>
            </div>

            <div className="itinerary-list">
              {stops &&
                stops.map((stop, idx) => {
                  let dotColorClass = 'dot-general';
                  let label = stop.stop_type.replace('_', ' ');

                  if (stop.stop_type === 'START') {
                    dotColorClass = 'dot-blue';
                    label = 'Start Location';
                  } else if (stop.stop_type === 'PICKUP') {
                    dotColorClass = 'dot-green';
                    label = 'Pickup Facility (Loading)';
                  } else if (stop.stop_type === 'DROPOFF') {
                    dotColorClass = 'dot-red';
                    label = 'Destination (Unloading)';
                  } else if (stop.stop_type === 'FUEL') {
                    dotColorClass = 'dot-amber';
                    label = 'Fuel Stop';
                  } else if (stop.stop_type === 'REST_30') {
                    dotColorClass = 'dot-sky';
                    label = '30-Minute Rest Break';
                  } else if (stop.stop_type === 'REST_10') {
                    dotColorClass = 'dot-slate';
                    label = '10-Hour Overnight Rest';
                  } else if (stop.stop_type === 'RESTART_34') {
                    dotColorClass = 'dot-pink';
                    label = '34-Hour Restart';
                  }

                  const isSelected = selectedStopIdx === idx;

                  return (
                    <div
                      key={idx}
                      className={`itinerary-item ${isSelected ? 'active-stop' : ''}`}
                      onClick={() => handleSelectItineraryStop(idx, stop)}
                    >
                      <div className={`itinerary-dot ${dotColorClass}`} />
                      <div className="itinerary-item-card">
                        <div className="itinerary-header-row">
                          <span className="itinerary-type">{label}</span>
                          <span className="itinerary-mile">Mile {stop.mile_marker}</span>
                        </div>
                        <div className="itinerary-location">{stop.name}</div>
                        <div className="itinerary-timing">
                          <span>
                            <strong>Arrive:</strong> {formatTimeOnly(stop.arrival_time, timezone)}
                          </span>
                          <span>
                            <strong>Depart:</strong> {formatTimeOnly(stop.departure_time, timezone)}
                          </span>
                          <span>
                            <strong>Duration:</strong> {formatHours(stop.duration_hours)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Right Column / Fullscreen Map Card */}
        <div className={`map-card-wrapper ${isFullscreen ? 'fullscreen-active' : ''} ${isNavigating ? 'nav-pitch-perspective' : ''}`}>
          {/* Leaflet Canvas Container */}
          <div ref={mapContainerRef} className="map-view-box" />

          {/* Floating Navigation HUD inside Map (Top-Left) */}
          {nextStop && (
            <div className="map-floating-hud-top">
              <div className="hud-next-stop-badge">
                <span className="hud-badge-tag">{isNavigating ? 'NEXT TURN / TARGET' : 'UPCOMING STOP'}</span>
                <span className="hud-stop-title">{nextStop.name.split(',')[0]} &bull; {nextStop.stop_type.replace('_', ' ')}</span>
              </div>
              {isNavigating && currentManeuver && (
                <div className="hud-maneuver-text">{currentManeuver.text}</div>
              )}
              <div className="hud-eta-row">
                <span>Arrival: {formatTimeOnly(nextStop.arrival_time, timezone)}</span>
                <span>&bull;</span>
                <span>Mile {nextStop.mile_marker}</span>
                <span>&bull;</span>
                <span>Duration {formatHours(nextStop.duration_hours)}</span>
              </div>
            </div>
          )}

          {/* Floating In-Map Action Controls (Top-Right / Thumb-friendly) */}
          <div className="map-floating-controls-panel">
            <button
              type="button"
              className={`map-ctrl-btn btn-nav-primary ${isNavigating ? 'nav-active' : ''}`}
              onClick={handleToggleNavigation}
              title={isNavigating ? 'Exit live navigation' : 'Start live turn-by-turn navigation'}
            >
              {isNavigating ? <RotateCcw size={16} /> : <Navigation2 size={16} />}
              <span>{isNavigating ? 'Exit' : 'Navigate'}</span>
            </button>

            {isNavigating && (
              <button
                type="button"
                className={`map-ctrl-btn ${isVoiceMuted ? 'btn-voice-muted' : ''}`}
                onClick={handleToggleVoice}
                title={isVoiceMuted ? 'Unmute voice guidance' : 'Mute voice guidance (does not stop navigation)'}
              >
                {isVoiceMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
                <span>{isVoiceMuted ? 'Muted' : 'Voice'}</span>
              </button>
            )}

            <button
              type="button"
              className="map-ctrl-btn"
              onClick={handleRecenter}
              title="Recenter and resume navigation follow"
            >
              <LocateFixed size={16} />
              <span>Location</span>
            </button>

            <button
              type="button"
              className="map-ctrl-btn"
              onClick={fitRouteBounds}
              title="Fit entire route on map"
            >
              <MapPin size={15} />
              <span>Fit</span>
            </button>

            <button
              type="button"
              className="map-ctrl-btn"
              onClick={handleToggleFullscreen}
              title={isFullscreen ? 'Exit Fullscreen' : 'Expand to Fullscreen Map'}
            >
              {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              <span>{isFullscreen ? 'Exit' : 'Fullscreen'}</span>
            </button>
          </div>

          {/* Floating Collapsible Legend Button (Bottom-Left) */}
          <div className="map-floating-legend-container">
            <button
              type="button"
              className="btn-legend-toggle"
              onClick={() => setShowLegend(!showLegend)}
            >
              <Layers size={14} />
              <span>Legend</span>
            </button>

            {showLegend && (
              <div className="legend-popup-menu">
                <div className="legend-popup-header">
                  <span>Map Legend</span>
                  <button type="button" onClick={() => setShowLegend(false)} className="btn-close-legend">
                    <X size={14} />
                  </button>
                </div>
                <div className="legend-items-list">
                  <div className="legend-item">
                    <span className="legend-dot blue-dot" />
                    <span>Start / Current Location</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot green-dot" />
                    <span>Pickup Facility</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot red-dot" />
                    <span>Drop-off Destination</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot amber-dot" />
                    <span>Fuel Stop (&le;1,000 mi)</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot sky-dot" />
                    <span>30-Min Rest Break</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot slate-dot" />
                    <span>10-Hour Overnight Rest</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-line teal-dash-line" />
                    <span>Approach Route (Start &rarr; Pickup)</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-line blue-solid-line" />
                    <span>Loaded Freight Route (Pickup &rarr; Drop)</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
