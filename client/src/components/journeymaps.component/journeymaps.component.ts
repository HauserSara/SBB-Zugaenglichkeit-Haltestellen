import { CUSTOM_ELEMENTS_SCHEMA, Component, NO_ERRORS_SCHEMA } from '@angular/core';
import { SbbNotificationModule } from '@sbb-esta/angular/notification';
import { SbbJourneyMapsModule } from '@sbb-esta/journey-maps';

declare global {
  interface Window {
    JM_API_KEY: string;
  }
}

/**
 * @title Journey Maps - Basic Example
 * @order 1
 */
@Component({
  selector: 'journeymaps.component',
  templateUrl: 'journeymaps.component.html',
  styleUrls: ['journeymaps.component.css'],
  standalone: true,
  imports: [
    SbbJourneyMapsModule,
    SbbNotificationModule
  ],
  schemas: [NO_ERRORS_SCHEMA]
})
export class JourneyMapsComponent {
  apiKey = window.JM_API_KEY;
}