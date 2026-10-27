import React, { useState, useEffect, useRef, useMemo } from 'react';
import Globe, { GlobeMethods } from 'react-globe.gl';
import { Earthquake } from '../types';
import { RotateCw, Compass } from 'lucide-react';

interface SeismicMapProps {
  events: Earthquake[];
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
}

type BasemapType = 'streets' | 'satellite';

export const SeismicMap: React.FC<SeismicMapProps> = ({
  events,
  selectedEventId,
  onSelectEvent
}) => {
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastPointClickedRef = useRef<number>(0);
  const [dimensions, setDimensions] = useState({ width: 800, height: 540 });
  const [activeBasemap, setActiveBasemap] = useState<BasemapType>('satellite');
  const [isRotating, setIsRotating] = useState(true);

  // Resize listener to fit parent card container responsively
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setDimensions({
          width: clientWidth || 800,
          height: clientHeight || 540
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    const timer = setTimeout(updateDimensions, 150);
    return () => {
      window.removeEventListener('resize', updateDimensions);
      clearTimeout(timer);
    };
  }, []);

  // Configure initial globe camera point of view
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.pointOfView({ lat: 20, lng: -40, altitude: 2.2 }, 0);
      const controls = globeRef.current.controls();
      if (controls) {
        controls.autoRotate = isRotating;
        controls.autoRotateSpeed = 0.6;
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
      }
    }
  }, [isRotating]);

  // Smoothly fly to selected earthquake, pause rotation, and zoom in automatically
  useEffect(() => {
    if (selectedEventId && globeRef.current) {
      const selected = events.find((e) => e.id === selectedEventId);
      if (selected) {
        // 1. Pause auto-rotation immediately
        setIsRotating(false);
        const controls = globeRef.current.controls();
        if (controls) {
          controls.autoRotate = false;
        }

        // 2. Automatic smooth close-up zoom into the seismic location
        globeRef.current.pointOfView(
          {
            lat: selected.latitude,
            lng: selected.longitude,
            altitude: 0.6
          },
          1400
        );
      }
    }
  }, [selectedEventId, events]);

  const getMarkerColor = (mag: number): string => {
    if (mag >= 6.0) return '#ef4444'; // Red
    if (mag >= 4.5) return '#f97316'; // Orange
    if (mag >= 3.0) return '#f59e0b'; // Amber
    return '#10b981'; // Emerald
  };

  const getRgbComponents = (mag: number): string => {
    if (mag >= 6.0) return '239, 68, 68';
    if (mag >= 4.5) return '249, 115, 22';
    if (mag >= 3.0) return '245, 158, 11';
    return '16, 185, 129';
  };

  // Generate ripple rings for high-magnitude or selected events
  const ringsData = useMemo(() => {
    return events.filter(
      (e) => e.mag >= 3.5 || e.id === selectedEventId || (e.tsunami && e.tsunami > 0)
    );
  }, [events, selectedEventId]);

  const globeTexture =
    activeBasemap === 'satellite'
      ? '/textures/earth-blue-marble.jpg'
      : '/textures/earth-night.jpg';

  const handleZoomOutAndResume = () => {
    // If a point was just clicked, do not zoom out
    if (Date.now() - lastPointClickedRef.current < 250) {
      return;
    }
    // Deselect current earthquake
    if (selectedEventId) {
      onSelectEvent('');
    }
    // Re-enable auto-rotation
    setIsRotating(true);
    const controls = globeRef.current?.controls();
    if (controls) {
      controls.autoRotate = true;
    }
    // Smoothly pull camera back into full globe overview
    globeRef.current?.pointOfView({ altitude: 2.2 }, 1200);
  };

  const resetView = () => {
    handleZoomOutAndResume();
    if (globeRef.current) {
      globeRef.current.pointOfView({ lat: 20, lng: -20, altitude: 2.2 }, 1000);
    }
  };

  return (
    <div
      ref={containerRef}
      onClick={(e) => {
        // If clicking background canvas outside of points
        if ((e.target as HTMLElement).tagName === 'CANVAS') {
          handleZoomOutAndResume();
        }
      }}
      className="relative w-full h-[540px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-[#030712] select-none"
    >
      <Globe
        ref={globeRef}
        width={dimensions.width}
        height={dimensions.height}
        globeImageUrl={globeTexture}
        bumpImageUrl="/textures/earth-topology.png"
        backgroundImageUrl="/textures/night-sky.png"
        atmosphereColor="#38bdf8"
        atmosphereAltitude={0.16}
        showAtmosphere={true}
        onGlobeClick={handleZoomOutAndResume}
        // Points layer
        pointsData={events}
        pointLat={(d: any) => d.latitude}
        pointLng={(d: any) => d.longitude}
        pointColor={(d: any) => getMarkerColor(d.mag)}
        pointAltitude={(d: any) =>
          d.id === selectedEventId
            ? 0.08
            : Math.min(0.12, Math.max(0.015, d.mag * 0.015))
        }
        pointRadius={(d: any) =>
          d.id === selectedEventId
            ? 0.95
            : Math.max(0.28, Math.min(0.85, d.mag * 0.12))
        }
        pointsMerge={false}
        onPointClick={(d: any) => {
          lastPointClickedRef.current = Date.now();
          onSelectEvent(d.id);
          setIsRotating(false);
          const controls = globeRef.current?.controls();
          if (controls) {
            controls.autoRotate = false;
          }
          globeRef.current?.pointOfView(
            {
              lat: d.latitude,
              lng: d.longitude,
              altitude: 0.6
            },
            1400
          );
        }}
        pointLabel={(d: any) => `
          <div style="background: rgba(3, 7, 18, 0.92); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 10px 12px; color: #f8fafc; font-family: sans-serif; font-size: 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); min-width: 200px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="background: ${getMarkerColor(d.mag)}; color: white; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px; font-family: monospace;">
                M ${d.mag.toFixed(1)}
              </span>
              <span style="color: #94a3b8; font-size: 11px; font-family: monospace;">
                ${new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <div style="font-weight: 600; color: #e2e8f0; margin-bottom: 6px; line-height: 1.3;">
              ${d.place || 'Ubicación sin especificar'}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px; color: #94a3b8;">
              <div>Prof: <b style="color: #cbd5e1;">${d.depth_km} km</b></div>
              <div>Lat/Lon: <b style="color: #cbd5e1;">${d.latitude.toFixed(1)}°, ${d.longitude.toFixed(1)}°</b></div>
            </div>
            ${
              d.tsunami > 0
                ? '<div style="margin-top: 6px; padding: 3px 6px; background: rgba(225, 29, 72, 0.15); border: 1px solid rgba(225, 29, 72, 0.3); border-radius: 4px; color: #f43f5e; font-weight: bold; font-size: 10px;">🌊 ALERTA DE TSUNAMI</div>'
                : ''
            }
          </div>
        `}
        // Animated seismic ripple rings
        ringsData={ringsData}
        ringLat={(d: any) => d.latitude}
        ringLng={(d: any) => d.longitude}
        ringColor={(d: any) => (t: number) =>
          `rgba(${getRgbComponents(d.mag)}, ${Math.max(0, (1 - t) * 0.75)})`
        }
        ringMaxRadius={(d: any) =>
          d.id === selectedEventId ? 6.5 : Math.max(2.5, Math.min(6.0, d.mag * 0.95))
        }
        ringPropagationSpeed={2.2}
        ringRepeatPeriod={1400}
      />

      {/* Top Right Controls: Terreno / Satélite, Rotación y Centrar */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
        <div className="bg-black/35 backdrop-blur-md p-1 rounded-lg border border-white/10 shadow-2xl flex items-center gap-1">
          <button
            onClick={() => setActiveBasemap('streets')}
            className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
              activeBasemap === 'streets'
                ? 'bg-sky-500/80 text-white shadow-sm backdrop-blur-sm'
                : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            Terreno
          </button>
          <button
            onClick={() => setActiveBasemap('satellite')}
            className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
              activeBasemap === 'satellite'
                ? 'bg-sky-500/80 text-white shadow-sm'
                : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            Satélite
          </button>
        </div>

        {/* Rotation and Reset Actions */}
        <div className="bg-black/35 backdrop-blur-md p-1 rounded-lg border border-white/10 shadow-2xl flex items-center gap-1">
          <button
            onClick={() => setIsRotating(!isRotating)}
            title={isRotating ? 'Pausar auto-rotación' : 'Activar auto-rotación'}
            className={`p-1.5 rounded text-xs transition-all ${
              isRotating
                ? 'bg-sky-500/80 text-white shadow-sm'
                : 'text-slate-300 hover:text-white hover:bg-white/10'
            }`}
          >
            <RotateCw className={`w-3.5 h-3.5 ${isRotating ? 'animate-spin-slow' : ''}`} />
          </button>
          <button
            onClick={resetView}
            title="Centrar globo"
            className="p-1.5 rounded text-slate-300 hover:text-white hover:bg-white/10 text-xs transition-all"
          >
            <Compass className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Bottom Left: Escala de Magnitud (Horizontal y Traslúcido) */}
      <div className="absolute bottom-4 left-4 z-20 bg-black/35 backdrop-blur-md px-3.5 py-2 rounded-lg border border-white/10 text-xs shadow-2xl">
        <div className="font-semibold text-slate-100 mb-1.5 text-[11px] tracking-wide">
          Escala de Magnitud
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50 shrink-0"></span>
            <span className="text-[11px] text-slate-200 font-medium">&lt; 3.0</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50 shrink-0"></span>
            <span className="text-[11px] text-slate-200 font-medium">3.0 - 4.4</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-sm shadow-orange-500/50 shrink-0"></span>
            <span className="text-[11px] text-slate-200 font-medium">4.5 - 5.9</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50 shrink-0"></span>
            <span className="text-[11px] text-slate-200 font-medium">&ge; 6.0</span>
          </div>
        </div>
      </div>

      {/* Bottom Right: Interactive hint pill */}
      <div className="absolute bottom-4 right-4 z-20 bg-black/30 backdrop-blur-md px-2.5 py-1 rounded-md border border-white/10 text-[10px] text-slate-400 font-mono hidden sm:block">
        Arrastra para rotar • Rueda para zoom
      </div>
    </div>
  );
};
