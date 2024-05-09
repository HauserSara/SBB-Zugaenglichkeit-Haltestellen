import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { Map , Marker} from 'maplibre-gl';

declare global {
  interface Window {
    JM_API_KEY: string;
  }
}

@Component({
  selector: 'map-main',
  templateUrl: './map-main.component.html',
  styleUrl: './map-main.component.css'
})
export class MapMain implements OnDestroy, AfterViewInit{
  apiKey = window.JM_API_KEY;

  private map!: Map;

  constructor() { }

  ngAfterViewInit(): void {
    this.map = new Map({
      container: 'map', // container ID
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`, // your MapTiler style URL
      center: [7.56, 46.85], // starting position [lng, lat]
      zoom: 10 // starting zoom
    });
    this.map.on('load', () => {
    });
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

}
