import { CUSTOM_ELEMENTS_SCHEMA, Component, NO_ERRORS_SCHEMA, NgModule } from '@angular/core';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SbbNotificationModule } from '@sbb-esta/angular/notification';
import { SbbJourneyMapsModule } from '@sbb-esta/journey-maps';

declare global {
  interface Window {
    JM_API_KEY: string;
  }
}

@NgModule({
  imports: [
    BrowserAnimationsModule,
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

}