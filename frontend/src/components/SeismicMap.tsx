import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { Earthquake } from '../types';
import { AlertTriangle, Compass, Waves } from 'lucide-react';

interface SeismicMapProps {
  events: Earthquake[];
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
}

export const SeismicMap: React.FC<SeismicMapProps> = ({
  events,
  selectedEventId,
  onSelectEvent
}) => {
  const getMarkerColor = (mag: number): string => {
    if (mag >= 6.0) return '#ef4444'; // Red
    if (mag >= 4.5) return '#f97316'; // Orange
    if (mag >= 3.0) return '#f59e0b'; // Amber
    return '#10b981'; // Green
  };

  const getMarkerRadius = (mag: number): number => {
    return Math.max(6, Math.min(24, Math.round(mag * 3.5)));
  };

  return (
    <div className="relative w-full h-[480px] rounded-xl overflow-hidden border border-slate-800 shadow-xl bg-slate-950">
      <MapContainer
        center={[20.0, 0.0]}
        zoom={2}
        minZoom={1.5}
        maxZoom={10}
        scrollWheelZoom={true}
        className="w-full h-full z-10"
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {events.map((ev) => {
          const isSelected = ev.id === selectedEventId;
          const color = getMarkerColor(ev.mag);
          const radius = getMarkerRadius(ev.mag);

          return (
            <CircleMarker
              key={ev.id}
              center={[ev.latitude, ev.longitude]}
              radius={isSelected ? radius + 4 : radius}
              pathOptions={{
                color: isSelected ? '#ffffff' : color,
                fillColor: color,
                fillOpacity: isSelected ? 0.9 : 0.75,
                weight: isSelected ? 3 : 1.5
              }}
              eventHandlers={{
                click: () => onSelectEvent(ev.id)
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1 min-w-[200px] text-slate-900">
                  <div className="flex items-center justify-between border-b pb-1 mb-2">
                    <span
                      className="text-xs font-bold px-2 py-0.5 rounded text-white"
                      style={{ backgroundColor: color }}
                    >
                      M {ev.mag}
                    </span>
                    <span className="text-[11px] text-slate-500">
                      {new Date(ev.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <p className="font-semibold text-xs leading-tight mb-2 text-slate-800">
                    {ev.place || 'Ubicación no especificada'}
                  </p>

                  <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-600 mb-2">
                    <div>Profundidad: <b>{ev.depth_km} km</b></div>
                    <div>Lat/Lon: <b>{ev.latitude.toFixed(1)}°, {ev.longitude.toFixed(1)}°</b></div>
                  </div>

                  {ev.tsunami > 0 && (
                    <div className="flex items-center gap-1.5 text-xs text-rose-600 font-bold bg-rose-50 p-1 rounded">
                      <Waves className="w-3.5 h-3.5" />
                      <span>Alerta de Tsunami</span>
                    </div>
                  )}

                  {ev.url && (
                    <a
                      href={ev.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-[11px] text-sky-600 hover:underline mt-2 text-right"
                    >
                      Ver en catálogo USGS &rarr;
                    </a>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Map Legend Floating Overlay */}
      <div className="absolute bottom-4 left-4 z-20 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-700/70 text-xs shadow-lg">
        <div className="font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
          <Compass className="w-3.5 h-3.5 text-sky-400" />
          <span>Escala de Magnitud</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span className="text-[11px] text-slate-400">&lt; 3.0</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span className="text-[11px] text-slate-400">3.0 - 4.4</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
            <span className="text-[11px] text-slate-400">4.5 - 5.9</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <span className="text-[11px] text-slate-400">&ge; 6.0</span>
          </div>
        </div>
      </div>
    </div>
  );
};
