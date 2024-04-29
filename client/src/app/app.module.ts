import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { RouterModule, Routes } from '@angular/router';

import { SbbButtonModule } from '@sbb-esta/angular/button';
import { SbbCheckboxModule } from '@sbb-esta/angular/checkbox';
import { SbbIconSidebar, SbbSidebar } from '@sbb-esta/angular/sidebar';
import { SbbIcon } from '@sbb-esta/angular/icon';
import { HttpClientModule } from '@angular/common/http';
import { SBB_SELECT_SCROLL_STRATEGY_PROVIDER } from '@sbb-esta/angular/select';
import { SbbDatepickerModule } from '@sbb-esta/angular/datepicker';

import { MapComponent } from './pages/map/map.component';
import { NavigateComponent } from './pages/navigate/navigate.component';
import { ControlsComponent } from './pages/controls/controls.component';

import { IconSidebarExample } from '../components/icon-sidebar-example/icon-sidebar-example';
import { JourneyMapsComponent } from '../components/journeymaps.component/journeymaps.component';

const appRoutes: Routes = [
  //set default route
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'map'
  },
  { path: 'map',  component: MapComponent },
  { path: 'navigate', component: NavigateComponent },
  { path: 'controls', component: ControlsComponent }
];


@NgModule({
  declarations: [
    AppComponent,
    ControlsComponent,
    NavigateComponent
  ],
  imports: [
    BrowserModule,
    SbbButtonModule,
    SbbCheckboxModule,
    SbbIconSidebar,
    SbbIcon,
    HttpClientModule,
    SbbDatepickerModule,
    RouterModule.forRoot(
      appRoutes, {enableTracing: true}
    ),
    IconSidebarExample,
    JourneyMapsComponent,
    MapComponent
  ],
  providers: [
    provideAnimationsAsync(),
    SBB_SELECT_SCROLL_STRATEGY_PROVIDER
  ],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA],
})
export class AppModule { }
