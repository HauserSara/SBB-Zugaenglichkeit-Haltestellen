import { Component, OnDestroy, AfterViewInit } from '@angular/core';
import maplibregl, { Map, Marker, LngLat, GeoJSONSource, AttributionControl } from 'maplibre-gl';
import { HttpClient } from '@angular/common/http';

declare global {
  interface Window { JM_API_KEY: string; }
}

@Component({
  selector: 'map-main',
  templateUrl: './map-main.component.html',
  styleUrls: ['./map-main.component.css']
})
export class MapMain implements OnDestroy, AfterViewInit {
  apiKey = window.JM_API_KEY;
  private map!: Map;
  public markers: Marker[] = [];

  constructor(private http: HttpClient) { }

  ngAfterViewInit(): void {
    this.map = new Map({
      container: 'map-main', 
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`,
      center: [8.2275, 46.8182], 
      zoom: 7.5, 
      attributionControl: false
    });

    this.initMap();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
    this.clearMarkers();
  }

  private initMap(): void {
    this.map.on('load', () => {
      this.map.on('click', (e) => this.handleMapClick(e.lngLat));
      this.addBaseLayer();
    });
  }

  private addBaseLayer(): void {
    this.map.addSource('swisstopo-height', {
      'type': 'raster',
      'tiles': [
        'https://wms.geo.admin.ch/?service=WMS&request=GetMap&layers=ch.swisstopo.pixelkarte-farbe&styles=default&format=image/png&transparent=true&version=1.3.0&crs=EPSG:3857&width=256&height=256&bbox={bbox-epsg-3857}'
      ],
      'tileSize': 256
    });

    this.map.addLayer({
      'id': 'swisstopo-height-layer',
      'type': 'raster',
      'source': 'swisstopo-height',
      'paint': { 'raster-opacity': 0.4 }
    });

    const attributionControl = new AttributionControl({compact: true});
    this.map.addControl(attributionControl, 'top-left');
  }

  private handleMapClick(lngLat: LngLat): void {
    if (this.markers.length >= 2) {
      this.clearMarkers();
      this.clearRoutes();
    }

    this.addMarker(lngLat);

    if (this.markers.length === 2) {
      this.getRoute();
    }
  }

  addMarker(lngLat: LngLat): void {
    const el = document.createElement('div');
    el.className = 'marker';
    el.style.backgroundImage = 'url(assets/icons/location-pin.svg)';
    el.style.width = '60px';
    el.style.height = '60px';
    el.style.backgroundSize = 'cover';

    const marker = new Marker({ element: el }).setLngLat(lngLat).addTo(this.map);
    this.markers.push(marker);
  }

  getRoute(): void {
    if (this.markers.length < 2) {
      return;
    }

    const url = 'http://127.0.0.1:8000/route_journeymaps/';
    const body = {
      "lat1": this.markers[0].getLngLat().lat,
      "lon1": this.markers[0].getLngLat().lng,
      "lat2": this.markers[1].getLngLat().lat,
      "lon2": this.markers[1].getLngLat().lng,
      "time": "12:00"
    };
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'sbb-a11y-app'
    };

    this.http.post<any>(url, body, { headers }).subscribe({
      next: (geojsonData) => this.displayGeoJSON(geojsonData),
      error: (error) => console.error("POST call in error", error.error),
      complete: () => console.log("The POST observable is now completed.")
    });
  }

  displayGeoJSON(responseData: any[]): void {
    this.clearRoutes(); // Clear existing routes before adding new ones
    responseData.forEach((item, index) => {
      const geoJSONData = item; // Directly using the item as GeoJSON data
      const sourceId = `route-${index}`;
      const layerId = `route-layer-${index}`;

      if (!this.map.getSource(sourceId)) {
        this.map.addSource(sourceId, {
          type: 'geojson',
          data: geoJSONData
        });

        this.map.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          layout: {},
          paint: {
            'line-color': '#FF0000',
            'line-width': 5
          }
        });

        if (index === 0 && geoJSONData.bbox) { // Auto-zoom to the first route
          this.map.fitBounds(geoJSONData.bbox, {padding: 20});
        }
      }
    });
  }

  clearMarkers(): void {
    this.markers.forEach(marker => marker.remove());
    this.markers = [];
  }

  clearRoutes(): void {
    if (this.map && this.map.getStyle()) {
      this.map.getStyle().layers.forEach(layer => {
        if (layer.id.startsWith('route-layer-') && this.map.getLayer(layer.id)) {
          this.map.removeLayer(layer.id);
        }
      });
      Object.keys(this.map.getStyle().sources).forEach(sourceId => {
        if (sourceId.startsWith('route-') && this.map.getSource(sourceId)) {
          this.map.removeSource(sourceId);
        }
      });
    }
  }
}
