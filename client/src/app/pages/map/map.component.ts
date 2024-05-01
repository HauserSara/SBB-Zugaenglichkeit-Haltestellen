import { CUSTOM_ELEMENTS_SCHEMA, Component, NO_ERRORS_SCHEMA, NgModule } from '@angular/core';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { JourneyMapsComponent } from '../../../components/journeymaps.component/journeymaps.component';
import { SbbNotificationModule } from '@sbb-esta/angular/notification';
import { SbbJourneyMapsModule, SbbFeaturesClickEventData, SbbFeaturesHoverChangeEventData, SbbFeatureData} from '@sbb-esta/journey-maps';

declare global {
  interface Window {
    JM_API_KEY: string;
  }
}

@NgModule({
  imports: [
    BrowserAnimationsModule,
    JourneyMapsComponent,
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA],
})
export class TrainChooChooAppModule {}

/**
 * @title Journey Maps - Basic Example
 * @order 1
 */

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrl: './map.component.css',
  standalone: true,
  imports: [
    SbbJourneyMapsModule,
    SbbNotificationModule
  ],
})

export class MapComponent {
  apiKey = window.JM_API_KEY;
  selectedCoordinates: string = '';

  constructor() { }

  // Event Handler für Klickereignisse
  onMapClick(eventData: SbbFeaturesClickEventData): void {
    // Hier erhältst du die Koordinaten des angeklickten Punktes
    const coordinates = eventData.clickLngLat;
    console.log('Klick-Koordinaten:', coordinates);

    // Hier könntest du die Koordinaten weiterverarbeiten, z.B. in einem Attribut speichern
    this.selectedCoordinates = `Latitude: ${coordinates.lat}, Longitude: ${coordinates.lng}`;
  }
}