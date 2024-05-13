import { Component, OnDestroy, AfterViewInit } from '@angular/core';
import { Map, Popup } from 'maplibre-gl';

declare global {
  interface Window {
    JM_API_KEY: string;
  }
}

@Component({
  selector: 'map-main',
  templateUrl: './map-main.component.html',
  styleUrls: ['./map-main.component.css']
})
export class MapMain implements OnDestroy, AfterViewInit {
  apiKey = window.JM_API_KEY;
  private map!: Map;

  constructor() { }

  ngAfterViewInit(): void {
    this.map = new Map({
      container: 'map', // Container-ID
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`,
      center: [7.56, 46.85], // Startposition [lng, lat]
      zoom: 10 // Startzoom
    });

    this.map.on('load', () => {
      const image = new Image(150, 150);
      image.onload = () => {
        this.map.addImage('cat', image);
        this.addGeoJsonLayer();
      };
      image.src = 'assets/icons/Toiletten.svg';
    });
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private addGeoJsonLayer(): void {
    fetch('assets/geojson/prm_toilets.geojson')
      .then(res => {
        if (!res.ok) {
          throw new Error('Netzwerkantwort war nicht ok');
        }
        return res.json();
      })
      .then(data => {
        this.map.addSource('prm_toilets', {
          type: 'geojson',
          data: data
        });

        this.map.addLayer({
          id: 'prm_toilets-layer',
          type: 'symbol',
          source: 'prm_toilets',
          layout: {
            'icon-image': 'cat',
            'icon-size': 0.1
          }
        });

        this.map.on('click', 'prm_toilets-layer', (e) => {
          if (e.features && e.features.length > 0) {
              const feature = e.features[0];
              if (feature.geometry.type === 'Point' && feature.geometry.coordinates.length === 2) {
                  const coordinates: [number, number] = [
                      feature.geometry.coordinates[0],
                      feature.geometry.coordinates[1]
                  ];
      
                  const wheelchairToilet = feature.properties['WHEELCHAIR_TOILET'];
                  const wheelchairAccess = wheelchairToilet === 1 ? 'Ja' : (wheelchairToilet === 2 ? 'Nein' : 'Unbekannt');

                  new Popup()
                      .setLngLat(coordinates)
                      .setHTML(`<strong>Rollstuhlgerechtes WC:</strong> ${wheelchairAccess}`)
                      .addTo(this.map);
              }
          }
      });
      
      })
      .catch(error => console.error('Fehler beim Laden des GeoJSON: ', error));
  }
}
