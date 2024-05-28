import { Component, OnDestroy, AfterViewInit } from '@angular/core';
import maplibregl, { Map, Marker, LngLat, GeoJSONSource, AttributionControl } from 'maplibre-gl';
import { HttpClient } from '@angular/common/http';
import { Feature, Geometry } from 'geojson';


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
      container: 'map-main', // container ID
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`, // your MapTiler style URL
      center: [8.2275, 46.8182], // starting position [lng, lat]
      zoom: 7.5, // starting zoom
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
      this.map.on('click', (e) => {
        this.handleMapClick(e.lngLat);
      });
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
        'paint': {
          // Set the opacity of the raster layer to 0.4, which corresponds to 60% transparency
          'raster-opacity': 0.4
        }
      });
    });
    const attributionControl = new AttributionControl({
      compact: true
    });
    this.map.addControl(attributionControl, 'top-left');
  }

  private handleMapClick(lngLat: LngLat): void {
    if (this.markers.length >= 2) {
      this.clearMarkers();
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
      return; // Ensure there are exactly two markers
    }

    const url = 'http://127.0.0.1:8000/route_journeymaps/';
    const body = {
      "lat1": this.markers[0].getLngLat().lng,
      "lon1": this.markers[0].getLngLat().lat,
      "lat2": this.markers[1].getLngLat().lng,
      "lon2": this.markers[1].getLngLat().lat,
      "time": "12:00"
    };
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'sbb-a11y-app'
    };

    console.log(`Sending POST request to ${url} with body:`, body);

    this.http.post<any>(url, body, { headers }).subscribe({
      next: (geojsonData) => this.displayGeoJSON(geojsonData),
      error: (error) => console.error("POST call in error", error.error),
      complete: () => console.log("The POST observable is now completed.")
    });
  }
  displayGeoJSON(responseData: any[]): void {
    responseData.forEach((item) => {
      const geoJSONData = item[1]; // Extrahieren des GeoJSON-Objekts
      const layerColor = '#FF0000';
      const sourceId = `route-${geoJSONData.features[0].properties.type}-${item[0]}`; // Eindeutige Source ID
      const layerId = `route-layer-${geoJSONData.features[0].properties.type}-${item[0]}`;
  
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
            'line-color': layerColor,
            'line-width': 5
          }
        });
      } else {
        // Update the source data if it already exists
        (this.map.getSource(sourceId) as GeoJSONSource).setData(geoJSONData);
      }
    });
  }
  

  clearMarkers(): void {
    this.markers.forEach(marker => marker.remove());
    this.markers = [];
    this.clearRoutes();
  }

  clearRoutes(): void {
    this.map.getStyle().layers?.forEach(layer => {
      if (layer.id.includes('route-layer-')) {
        this.map.removeLayer(layer.id)
      }
    });
  }
}
