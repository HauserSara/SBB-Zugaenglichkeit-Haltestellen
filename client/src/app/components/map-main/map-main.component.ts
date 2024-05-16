import { Component, OnDestroy, AfterViewInit, OnInit } from '@angular/core';
import { Map, Popup } from 'maplibre-gl';

declare global {
  interface Window { JM_API_KEY: string; }
}

interface LayerProperties {
  [key: string]: 'boolean' | 'text';
}

@Component({
  selector: 'map-main',
  templateUrl: './map-main.component.html',
  styleUrls: ['./map-main.component.css']
})
export class MapMain implements OnDestroy, AfterViewInit, OnInit {
  apiKey = window.JM_API_KEY;
  private map!: Map;
  isChecked: boolean = false;
  private validSLOIDValues: string[] = []; 

  constructor() { }

  ngOnInit() {}

  ngAfterViewInit(): void {
    this.initializeMap();
  }

  onToggleChange(isChecked: boolean): void {
    this.isChecked = isChecked;
    this.updateMode();
  }

  updateMode(): void {
    if (this.isChecked) {
      this.setupConnectionMode();
    } else {
      this.setupInformationMode();
    }
  }

  setupInformationMode(): void {
    console.log('Information mode activated');
    this.removeAllLayers();
    this.addGeoJsonLayer();
  }

  setupConnectionMode(): void {
    console.log('Connection mode activated');
    this.removeAllLayers();
    this.addAllPointsLayer();  // Fügt den gefilterten Layer hinzu
  }  

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initializeMap(): void {
    this.map = new Map({
      container: 'map',
      style: `https://journey-maps-tiles.geocdn.sbb.ch/styles/base_bright_v2/style.json?api_key=${this.apiKey}`,
      center: [7.56, 46.85],
      zoom: 10
    });

    this.map.on('load', () => {
      const icons = {
        'toilet-icon': 'assets/icons/Toiletten.svg',
        'parking-icon': 'assets/icons/Parkplatz.svg',
        'info-desk-icon': 'assets/icons/Informationsdesk.svg',
        'ticket-counter-icon': 'assets/icons/Ticket.svg'
      };

      Object.entries(icons).forEach(([key, src]) => {
        const image = new Image(200, 200);
        image.onload = () => this.map.addImage(key, image);
        image.src = src;
      });

      this.initializeSource();
      this.setupInformationMode();
    });
  }

  private initializeSource(): void {
    const sources = {
      'prm_toilets': 'assets/geojson/prm_toilets.geojson',
      'prm_parking_lots': 'assets/geojson/prm_parking_lots.geojson',
      'prm_info_desks': 'assets/geojson/prm_info_desks.geojson',
      'prm_ticket_counters': 'assets/geojson/prm_ticket_counters.geojson',
      'all_points': 'assets/geojson/all_points.geojson' // Hinzufügen der neuen Quelle
    };
  
    Promise.all(
      Object.entries(sources).map(([key, url]) =>
        fetch(url)
          .then(res => {
            if (!res.ok) throw new Error(`Network response was not ok for ${key}`);
            return res.json();
          })
          .then(data => {
            if (!this.map.getSource(key)) {
              this.map.addSource(key, {
                type: 'geojson',
                data: data
              });
            }
          })
      )
    ).then(() => {
      this.setupInformationMode(); // Dies wird aufgerufen, wenn alle Quellen geladen sind
    }).catch(error => console.error("Error loading the GeoJSON: ", error));
  }  

  private addAllPointsLayer(): void {
    if (!this.map.getLayer('all_points-layer') && this.map.getSource('all_points')) {
      this.map.addLayer({
        id: 'all_points-layer',
        type: 'circle',
        source: 'all_points',
        paint: {
          'circle-radius': 5,
          'circle-color': '#FF0000'  // Roter Kreis als Markierung
        }
      });
  
      // Klickevent für Punkte, um Filter basierend auf SLOID zu setzen
      this.setupClickHandlerForFilter();
    }
  }
  
  
  private addGeoJsonLayer(): void {
    const layers: { [id: string]: { source: string, icon: string, properties: LayerProperties } } = {
      'prm_toilets-layer': { 
        source: 'prm_toilets', 
        icon: 'toilet-icon', 
        properties: {'WHEELCHAIR_TOILET': 'boolean'} // Correctly typed as 'boolean'
      },
      'prm_parking_lots-layer': { 
        source: 'prm_parking_lots', 
        icon: 'parking-icon', 
        properties: {'INFO': 'text', 'PRM_PLACES_AVAILABLE': 'boolean'} // Correctly typed as 'text' and 'boolean'
      },
      'prm_info_desks-layer': { 
        source: 'prm_info_desks', 
        icon: 'info-desk-icon', 
        properties: {'INDUCTION_LOOP': 'boolean', 'OPEN_HOURS': 'text', 'WHEELCHAIR_ACCESS': 'boolean'} // Correctly typed
      },
      'prm_ticket_counters-layer': { 
        source: 'prm_ticket_counters', 
        icon: 'ticket-counter-icon', 
        properties: {'DESCRIPTION': 'text', 'WHEELCHAIR_ACCESS': 'boolean'} // Correctly typed
      }
    };    

    Object.entries(layers).forEach(([id, { source, icon, properties }]) => {
      if (this.map.getSource(source) && !this.map.getLayer(id)) {
        this.map.addLayer({
          id: id,
          type: 'symbol',
          source: source,
          layout: {
            'icon-image': icon,
            'icon-size': 0.1,
            'visibility': 'visible'
          }
        });

        this.setupLayerClickHandler(id, properties);
      }
    });
  }

  private setupClickHandlerForFilter(): void {
    this.map.on('click', 'all_points-layer', (e) => {
      // Sicherstellen, dass Features vorhanden und nicht leer sind
      if (e.features && e.features.length > 0) {
        const clickedSLOID = e.features[0].properties['SLOID']; // Korrigierter Zugriff auf SLOID
        // Setze Filter nur für diesen SLOID
        this.validSLOIDValues = [clickedSLOID];

        // api service call to get the related SLOIDs
        
        //this.map.setFilter('all_points-layer', ['in', ['get', 'SLOID'], ['literal', this.validSLOIDValues]]);

      }
    });
  }
  
  public resetFilter(): void {
    if (this.map.getLayer('all_points-layer')) {
      this.map.setFilter('all_points-layer', null);  // Entfernt den Filter
    }
  }  

  public updateSLOIDFilter(newValues: string[]): void {
    this.validSLOIDValues = newValues;
    if (this.map.getLayer('all_points-layer')) {
      this.map.setFilter('all_points-layer', ['in', ['get', 'SLOID'], ['literal', this.validSLOIDValues]]);
    }
  }

  private setupLayerClickHandler(layerId: string, propertiesToShow: { [key: string]: 'boolean' | 'text' }): void {
    this.map.on('click', layerId, (e) => {
      if (e.features && e.features.length > 0) {
        const feature = e.features[0];
        if (feature.geometry.type === 'Point' && feature.geometry.coordinates.length === 2) {
          // Hier wird der Wert von 'Bezeichnung' überprüft
          const designation = feature.properties['Bezeichnung'];  // Nehmen Sie an, dass 'Bezeichnung' der richtige Schlüssel ist
          if (designation === 'Referenzpunkt') {
            console.log("Ja");
          } else {
            console.log("Nein");
          }

          const coordinates: [number, number] = [feature.geometry.coordinates[0], feature.geometry.coordinates[1]];
          let popupContent = '<div style="font-size: 12px;">';

          Object.entries(propertiesToShow).forEach(([prop, type]) => {
            let propValue = feature.properties[prop];
            let translatedProp = this.attributeTranslations[prop] || prop; // Verwendung der deutschen Übersetzung
            if (type === 'boolean') {
              propValue = propValue === 1 ? 'Ja' : (propValue === 2 ? 'Nein' : 'Unbekannt');
            }
            popupContent += `<strong>${translatedProp}:</strong> ${propValue}<br>`;
          });

          popupContent += '</div>';

          new Popup()
            .setLngLat(coordinates)
            .setHTML(popupContent)
            .addTo(this.map);
        }
      }
    });
  }

  
  private removeAllLayers(): void {
    const layerIds = ['prm_toilets-layer', 'prm_parking_lots-layer', 'prm_info_desks-layer', 'prm_ticket_counters-layer', 'all_points-layer'];
    layerIds.forEach(layerId => {
      if (this.map.getLayer(layerId)) {
        this.map.removeLayer(layerId);
      }
    });
  }

  private attributeTranslations: { [key: string]: string } = {
    'WHEELCHAIR_TOILET': 'Rollstuhlgerechtes WC',
    'INFO': 'Information',
    'PRM_PLACES_AVAILABLE': 'PRM Plätze verfügbar',
    'INDUCTION_LOOP': 'Induktionsschleife',
    'OPEN_HOURS': 'Öffnungszeiten',
    'WHEELCHAIR_ACCESS': 'Rollstuhlzugang',
    'DESCRIPTION': 'Beschreibung'
  };
  
}
