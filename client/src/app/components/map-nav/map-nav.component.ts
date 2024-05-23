import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { Map , Marker, LngLat, GeoJSONSource, AttributionControl} from 'maplibre-gl';
import { HttpClient } from '@angular/common/http';

declare global {
  interface Window { JM_API_KEY: string }
}

@Component({
  selector: 'map-nav',
  templateUrl: './map-nav.component.html',
  styleUrl: './map-nav.component.css'
})
export class MapNav implements OnInit, OnDestroy {
  apiKey = window.JM_API_KEY;
  private map!: Map;
  public markers: Marker[] = [];
  
  constructor(private http:HttpClient) { }
  

  ngOnInit(): void {
    this.initMap();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
    this.clearMarkers();
  }

  private initMap(): void {
    if (this.map) {
      this.map.remove();  // Clean up the existing map before creating a new one
    }

    this.map = new Map({
      container: 'map', // container ID
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`, // your MapTiler style URL
      center: [8.2275, 46.8182], // starting position [lng, lat]
      zoom: 7.5, // starting zoom
      attributionControl: false
    });

    this.map.on('load', () => {
      this.map.on('click', (e) => {
        this.handleMapClick(e.lngLat);
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

    const marker = new Marker({ element: el, anchor: 'bottom' }).setLngLat(lngLat).addTo(this.map);
    this.markers.push(marker);
  }

  //nur für testzwecke kann nacher gelöscht werden
  sendagain(): void {
    this.http.post<any>('http://127.0.0.1:8000/route_journeymaps/', {
      "lat1": this.markers[0].getLngLat().lng,
      "lon1": this.markers[0].getLngLat().lat,
      "lat2": this.markers[1].getLngLat().lng,
      "lon2": this.markers[1].getLngLat().lat,
      "time": "12:00"
    }, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'sbb-a11y-app'
      }
    }).subscribe({
      next: (geojsonData) => this.displayGeoJSON(geojsonData),
      error: (error) => console.error("POST call in error", error),
      complete: () => console.log("The POST observable is now completed.")
    });
  }


  getRoute(): void {
    if (this.markers.length < 2) {
      return; // Ensure there are exactly two markers
    }

  //   this.http.post<any>('http://127.0.0.1:8000/route_journeymaps/', {
  //     "lat1": this.markers[0].getLngLat().lng,
  //     "lon1": this.markers[0].getLngLat().lat,
  //     "lat2": this.markers[1].getLngLat().lng,
  //     "lon2": this.markers[1].getLngLat().lat,
  //     "time": "12:00"
  //   }, {
  //     headers: {
  //       'Content-Type': 'application/json',
  //       'User-Agent': 'sbb-a11y-app'
  //     }
  //   }).subscribe({
  //     next: (geojsonData) => this.displayGeoJSON(geojsonData),
  //     error: (error) => console.error("POST call in error", error.error),
  //     complete: () => console.log("The POST observable is now completed.")
  //   });
  // }

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

  displayGeoJSON(geoJSONData: any[]) {
    const layerColor = '#FF0000'; // Definiere eine konstante Farbe für alle Schichten

    geoJSONData.forEach((featureCollection, index) => {
      const sourceId = `route-${index}`;
      const layerId = `route-layer-${index}`;

      if (!this.map.getSource(sourceId)) {
        this.map.addSource(sourceId, {
          type: 'geojson',
          data: featureCollection
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
        (this.map.getSource(sourceId) as GeoJSONSource).setData(featureCollection);
      }

      // Zoom zur Bounding Box des ersten Features, wenn index == 0
      if (index === 0 && featureCollection.bbox) {
        this.map.fitBounds(featureCollection.bbox as [number, number, number, number], {
          padding: 20 // Optionaler Padding-Wert
        });
      }

    });
  }

clearRoutes(): void {
    if (this.map && this.map.getStyle()) {
        this.map.getStyle().layers.forEach(layer => {
            // Only attempt to remove the layer if it actually exists
            if (this.map.getLayer(layer.id)) {
                this.map.removeLayer(layer.id);
            }
        });
    }
}

  clearMarkers(): void {
    this.markers.forEach(marker => marker.remove());
    this.markers = [];
    this.clearRoutes();
  }
}
