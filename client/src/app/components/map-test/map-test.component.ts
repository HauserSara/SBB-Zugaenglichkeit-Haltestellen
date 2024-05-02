import { Component, OnInit, OnDestroy } from '@angular/core';
import { Map , Marker} from 'maplibre-gl';
import { SbbIcon } from '@sbb-esta/angular/icon';

declare global {
  interface Window {
    JM_API_KEY: string;
  }
}

@Component({
  selector: 'map-test',
  templateUrl: './map-test.component.html',
  styleUrl: './map-test.component.css'
})
export class MapTestComponent implements OnInit, OnDestroy {
  apiKey = window.JM_API_KEY;

  private map!: Map;
  public markers: Marker[] = [];
  clickedLat: number = 0;
  clickedLng: number = 0;

  constructor() { }

  ngOnInit(): void {
    this.initMap();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap(): void {
    this.map = new Map({
      container: 'map', // container ID
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`, // your MapTiler style URL
      center: [8.2275, 46.8182], // starting position [lng, lat]
      zoom: 7.5 // starting zoom
    });
    this.map.on('load', () => {
      this.map.on('click', (e) => {
        if (this.markers.length < 2) {  // Maximal zwei Marker erlauben
          this.addMarker(e.lngLat);
        }
      });
    });
  }

  addMarker(lngLat: maplibregl.LngLat): void {
    const el = document.createElement('div');
    el.className = 'marker';
    el.style.backgroundImage = 'url(assets/icons/location-pin.svg)';
    el.style.width = '60px';
    el.style.height = '60px';
    el.style.backgroundSize = 'cover';

    const marker = new Marker({ element: el })
      .setLngLat(lngLat)
      .addTo(this.map);
    this.markers.push(marker);
  }

  clearMarkers(): void {
    this.markers.forEach(marker => marker.remove());
    this.markers = [];
  }
}
