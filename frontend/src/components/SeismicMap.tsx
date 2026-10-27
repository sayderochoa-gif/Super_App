import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { Earthquake } from '../types';
import { Compass, Waves, Layers } from 'lucide-react';

interface SeismicMapProps {
  events: Earthquake[];
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
}

type BasemapType = 'streets' | 'satellite' | 'voyager' | 'dark';

interface BasemapConfig {
  name: string;
  url: string;
  attribution: string;
  maxZoom: number;
}

const BASEMAPS: Record<BasemapType, BasemapConfig> = {
  streets: {
    name: 'Mapa Estándar (OSM)',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  },
  satellite: {
    name: 'Satélite (Esri)',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri, Maxar, Earthstar Geographics',
    maxZoom: 18
  },
  voyager: {
    name: 'Cartográfico (Voyager)',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19
  },
  dark: {
    name: 'Modo Oscuro (Carto)',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19
  }
};

function MapController({ selectedCoords }: { selectedCoords: [number, number] | null }) {
  const map = useMap();

  useEffect(() => {
    // Force Leaflet to recalculate container bounds so all tiles load immediately
    map.invalidateSize();
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (selectedCoords) {
      map.flyTo(selectedCoords, Math.max(map.getZoom(), 5), { duration: 1.2 });
    }
  }, [selectedCoords, map]);

  return null;
}

export const SeismicMap: React.FC<SeismicMapProps> = ({
  events,
  selectedEventId,
  onSelectEvent
}) => {
  const [activeBasemap, setActiveBasemap] = useState<BasemapType>('streets');

  const selectedEvent = events.find((e) => e.id === selectedEventId);
  const selectedCoords: [number, number] | null = selectedEvent
    ? [selectedEvent.latitude, selectedEvent.longitude]
    : null;

  const getMarkerColor = (mag: number): string => {
    if (mag >= 6.0) return '#ef4444'; // Red
    if (mag >= 4.5) return '#f97316'; // Orange
    if (mag >= 3.0) return '#f59e0b'; // Amber
    return '#10b981'; // Green
  };

  const getMarkerRadius = (mag: number): number => {
    return Math.max(5, Math.min(22, Math.round(mag * 3.2)));
  };

  const currentBasemap = BASEMAPS[activeBasemap];

  return (
    <div className="relative w-full h-[520px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-900">
      <MapContainer
        center={[20.0, 0.0]}
        zoom={2}
        minZoom={1.5}
        maxZoom={12}
        scrollWheelZoom={true}
        className="w-full h-full z-10"
      >
        <MapController selectedCoords={selectedCoords} />

        <TileLayer
          key={activeBasemap}
          url={currentBasemap.url}
          attribution={currentBasemap.attribution}
          maxZoom={currentBasemap.maxZoom}
        />

        {events.map((ev) => {
          const isSelected = ev.id === selectedEventId;
          const color = getMarkerColor(ev.mag);
          const radius = getMarkerRadius(ev.mag);

          return (
            <CircleMarker
              key={ev.id}
              center={[ev.latitude, ev.longitude]}
              radius={isSelected ? radius + 5 : radius}
              pathOptions={{
                color: isSelected ? '#ffffff' : color,
                fillColor: color,
                fillOpacity: isSelected ? 0.95 : 0.8,
                weight: isSelected ? 3.5 : 1.5
              }}
              eventHandlers={{
                click: () => onSelectEvent(ev.id)
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1 min-w-[210px] text-slate-900">
                  <div className="flex items-center justify-between border-b pb-1 mb-2">
                    <span
                      className="text-xs font-bold px-2 py-0.5 rounded text-white shadow-sm"
                      style={{ backgroundColor: color }}
                    >
                      M {ev.mag.toFixed(1)}
                    </span>
                    <span className="text-[11px] text-slate-500 font-medium">
                      {new Date(ev.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <p className="font-semibold text-xs leading-snug mb-2 text-slate-800">
                    {ev.place || 'Ubicación sin especificar'}
                  </p>

                  <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-600 mb-2">
                    <div>Profundidad: <b>{ev.depth_km} km</b></div>
                    <div>Lat/Lon: <b>{ev.latitude.toFixed(1)}°, {ev.longitude.toFixed(1)}°</b></div>
                  </div>

                  {ev.tsunami > 0 && (
                    <div className="flex items-center gap-1.5 text-xs text-rose-600 font-bold bg-rose-50 p-1 rounded border border-rose-200">
                      <Waves className="w-3.5 h-3.5" />
                      <span>Alerta de Tsunami</span>
                    </div>
                  )}

                  {ev.url && (
                    <a
                      href={ev.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-[11px] text-sky-600 hover:text-sky-800 hover:underline mt-2 text-right font-medium"
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

      {/* Basemap Switcher Controls (Top Right) */}
      <div className="absolute top-4 right-4 z-20 bg-slate-900/90 backdrop-blur-md p-1.5 rounded-lg border border-slate-700/80 shadow-xl flex items-center gap-1">
        <div className="px-2 py-1 text-[11px] font-bold text-slate-300 flex items-center gap-1 border-r border-slate-700/80 mr-1">
          <Layers className="w-3 h-3 text-sky-400" />
          <span className="hidden sm:inline">Capa Base:</span>
        </div>
        <button
          onClick={() => setActiveBasemap('streets')}
          className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
            activeBasemap === 'streets'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
        >
          🗺️ Terreno
        </button>
        <button
          onClick={() => setActiveBasemap('satellite')}
          className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
            activeBasemap === 'satellite'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
        >
          🛰️ Satélite
        </button>
        <button
          onClick={() => setActiveBasemap('voyager')}
          className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
            activeBasemap === 'voyager'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
        >
          🧭 Claro
        </button>
        <button
          onClick={() => setActiveBasemap('dark')}
          className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
            activeBasemap === 'dark'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-300 hover:text-white hover:bg-slate-800'
          }`}
        >
          🌑 Oscuro
        </button>
      </div>

      {/* Map Legend Floating Overlay (Bottom Left) */}
      <div className="absolute bottom-4 left-4 z-20 bg-slate-900/90 backdrop-blur-md px-3.5 py-2.5 rounded-lg border border-slate-700/80 text-xs shadow-xl">
        <div className="font-semibold text-slate-200 mb-1.5 flex items-center gap-1.5">
          <Compass className="w-3.5 h-3.5 text-sky-400" />
          <span>Escala de Magnitud</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
            <span className="text-[11px] text-slate-300 font-medium">&lt; 3.0</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50"></span>
            <span className="text-[11px] text-slate-300 font-medium">3.0 - 4.4</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-sm shadow-orange-500/50"></span>
            <span className="text-[11px] text-slate-300 font-medium">4.5 - 5.9</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50"></span>
            <span className="text-[11px] text-slate-300 font-medium">&ge; 6.0</span>
          </div>
        </div>
      </div>
    </div>
  );
};
