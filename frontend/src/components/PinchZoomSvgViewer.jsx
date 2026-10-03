import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Maximize2 } from 'lucide-react';

export default function PinchZoomSvgViewer({ svgContent, className = '', nativeWidth = 1000, nativeHeight = 1180 }) {
  const containerRef = useRef(null);
  const contentRef = useRef(null);

  const minScale = 0.30; // Allows zooming out on phone viewports
  const maxScale = 3.50; // Allows deep zoom into 15-minute intervals and remarks

  // Separate Desktop and Mobile default scale
  const [scale, setScale] = useState(() => (typeof window !== 'undefined' && window.innerWidth <= 768 ? 0.30 : 1.0));
  const [fitScale, setFitScale] = useState(() => (typeof window !== 'undefined' && window.innerWidth <= 768 ? 0.30 : 1.0));
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isInteracting, setIsInteracting] = useState(false);

  // Desktop & Mobile calculateFitScale based on available container dimensions
  const calculateFitScale = useCallback(() => {
    const isMobileViewport = typeof window !== 'undefined' && window.innerWidth <= 768;

    if (isMobileViewport) {
      // Mobile/Phone: Keep existing scale calculation / 30% scale
      if (!containerRef.current) return 0.30;
      const containerWidth = containerRef.current.clientWidth;
      if (containerWidth <= 0) return 0.30;
      const availableWidth = Math.max(280, containerWidth - 12);
      const calculated = Number((availableWidth / nativeWidth).toFixed(3));
      return Math.max(minScale, Math.min(1.45, calculated));
    }

    // Desktop: Calculate true fit so the entire 1000x1180 paper fits comfortably inside the container width
    let containerWidth = 0;
    if (containerRef.current && containerRef.current.clientWidth > 0) {
      containerWidth = containerRef.current.clientWidth;
    } else if (typeof window !== 'undefined') {
      containerWidth = Math.min(1200, Math.max(768, window.innerWidth - 64));
    } else {
      containerWidth = 1000;
    }

    const availableWidth = Math.max(600, containerWidth - 24);
    // Fit the complete 1000px width inside available desktop container width (typically 0.80 - 1.15)
    const fit = Number((availableWidth / nativeWidth).toFixed(3));
    return Math.max(0.60, Math.min(1.15, fit));
  }, [nativeWidth, minScale]);

  // Initial and window resize / tab change scale fitting
  useEffect(() => {
    const handleResize = () => {
      const bestFit = calculateFitScale();
      setFitScale(bestFit);
      setScale((prev) => {
        // If at or near previous fit scale or initial load, adjust automatically to new container fit
        if (Math.abs(prev - fitScale) < 0.1 || prev <= 1.0) {
          setPan({ x: 0, y: 0 });
          return bestFit;
        }
        return prev;
      });
    };

    handleResize();

    let resizeObserver = null;
    if (typeof ResizeObserver !== 'undefined' && containerRef.current) {
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          if (entry.contentRect && entry.contentRect.width > 0) {
            handleResize();
          }
        }
      });
      resizeObserver.observe(containerRef.current);
    }

    window.addEventListener('resize', handleResize);
    return () => {
      if (resizeObserver) resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [calculateFitScale, fitScale, svgContent]);

  // State refs for smooth gesture tracking without stale closures
  const stateRef = useRef({
    scale: 1.0,
    pan: { x: 0, y: 0 },
    startDistance: 0,
    startScale: 1.0,
    startPan: { x: 0, y: 0 },
    startPoint: { x: 0, y: 0 },
    lastTap: 0,
    isDragging: false,
  });

  stateRef.current.scale = scale;
  stateRef.current.pan = pan;

  const handleZoomIn = () => {
    setScale((prev) => Math.min(maxScale, Number((prev + 0.25).toFixed(2))));
  };

  const handleZoomOut = () => {
    setScale((prev) => {
      const next = Math.max(minScale, Number((prev - 0.25).toFixed(2)));
      if (next <= fitScale) {
        setPan({ x: 0, y: 0 });
      }
      return next;
    });
  };

  const handleFit = () => {
    const bestFit = calculateFitScale();
    setScale(bestFit);
    setPan({ x: 0, y: 0 });
  };

  // Touch gesture handlers (Pinch in/out, double-tap, and single-touch pan)
  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      // 2-finger pinch
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      stateRef.current.startDistance = dist;
      stateRef.current.startScale = stateRef.current.scale;
      setIsInteracting(true);
    } else if (e.touches.length === 1) {
      const now = Date.now();
      const lastTap = stateRef.current.lastTap;
      stateRef.current.lastTap = now;

      // Double-tap: toggle between fitted scale and 2.0x
      if (now - lastTap < 300) {
        if (stateRef.current.scale > fitScale * 1.15) {
          handleFit();
        } else {
          setScale(2.0);
          setPan({ x: 0, y: 0 });
        }
        return;
      }

      // 1-finger pan tracking
      const t = e.touches[0];
      stateRef.current.startPoint = { x: t.clientX, y: t.clientY };
      stateRef.current.startPan = { ...stateRef.current.pan };
      stateRef.current.isDragging = true;
      setIsInteracting(true);
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2 && stateRef.current.startDistance > 0) {
      e.preventDefault(); // Stop outer webpage from zooming
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const currentDist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
      const ratio = currentDist / stateRef.current.startDistance;
      const targetScale = Math.max(minScale, Math.min(maxScale, Number((stateRef.current.startScale * ratio).toFixed(2))));
      setScale(targetScale);
    } else if (e.touches.length === 1 && stateRef.current.isDragging && stateRef.current.scale > fitScale) {
      // When zoomed in, allow internal panning within the viewer
      e.preventDefault();
      const t = e.touches[0];
      const dx = t.clientX - stateRef.current.startPoint.x;
      const dy = t.clientY - stateRef.current.startPoint.y;
      setPan({
        x: stateRef.current.startPan.x + dx,
        y: stateRef.current.startPan.y + dy,
      });
    }
  };

  const handleTouchEnd = () => {
    stateRef.current.startDistance = 0;
    stateRef.current.isDragging = false;
    setIsInteracting(false);
  };

  // Mouse pan handlers for desktop testing
  const handleMouseDown = (e) => {
    if (scale <= fitScale) return;
    stateRef.current.startPoint = { x: e.clientX, y: e.clientY };
    stateRef.current.startPan = { ...stateRef.current.pan };
    stateRef.current.isDragging = true;
    setIsInteracting(true);

    const handleMouseMove = (moveEvent) => {
      if (!stateRef.current.isDragging) return;
      const dx = moveEvent.clientX - stateRef.current.startPoint.x;
      const dy = moveEvent.clientY - stateRef.current.startPoint.y;
      setPan({
        x: stateRef.current.startPan.x + dx,
        y: stateRef.current.startPan.y + dy,
      });
    };

    const handleMouseUp = () => {
      stateRef.current.isDragging = false;
      setIsInteracting(false);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const dynamicHeight = Math.round(nativeHeight * scale + 16);

  return (
    <div
      ref={containerRef}
      className={`pinch-zoom-viewport-container ${className}`}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      style={{
        position: 'relative',
        overflow: scale > fitScale ? 'auto' : 'hidden',
        height: `${dynamicHeight}px`,
        minHeight: `${Math.min(320, dynamicHeight)}px`,
        maxHeight: 'none',
        width: '100%',
        maxWidth: '100%',
        userSelect: 'none',
        touchAction: scale > fitScale ? 'none' : 'pan-x pan-y',
        cursor: scale > fitScale ? (isInteracting ? 'grabbing' : 'grab') : 'default',
        transition: isInteracting ? 'none' : 'height 0.18s ease-out',
      }}
    >
      {/* Floating Zoom & Scale Control HUD */}
      <div className="pinch-zoom-hud-bar">
        <button
          type="button"
          className="btn-pinch-ctrl"
          onClick={handleZoomOut}
          disabled={scale <= minScale}
          title="Zoom Out (−)"
          aria-label="Zoom out"
        >
          <ZoomOut size={15} />
        </button>

        <span className="pinch-zoom-scale-badge" title="Current Zoom Scale">
          {Math.round(scale * 100)}%
        </span>

        <button
          type="button"
          className="btn-pinch-ctrl"
          onClick={handleZoomIn}
          disabled={scale >= maxScale}
          title="Zoom In (+)"
          aria-label="Zoom in"
        >
          <ZoomIn size={15} />
        </button>

        <button
          type="button"
          className="btn-pinch-ctrl btn-reset-zoom"
          onClick={handleFit}
          title="Fit entire log to screen"
          aria-label="Fit to screen"
        >
          <Maximize2 size={12} />
          <span>Fit</span>
        </button>
      </div>

      {/* Pannable & Scalable SVG Canvas Container */}
      <div
        ref={contentRef}
        className="pinch-zoom-canvas"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
          transformOrigin: '0 0',
          transition: isInteracting ? 'none' : 'transform 0.18s ease-out',
          width: `${nativeWidth}px`,
          minWidth: `${nativeWidth}px`,
        }}
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
    </div>
  );
}
