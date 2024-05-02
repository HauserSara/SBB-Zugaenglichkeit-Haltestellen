import { Component } from '@angular/core';

@Component({
  selector: 'app-controls',
  templateUrl: './controls.component.html',
  styleUrls: ['./controls.component.css']
})
export class ControlsComponent {
  accessibility = false;
  guidanceMarkings = false;

  onToggleChange(event: {id: string, checked: boolean}) {
    if (event.id === 'accessibility') {
      this.accessibility = event.checked;
      console.log('Accessibility Toggle status:', event.checked);
    } else if (event.id === 'guidancemarkings') {
      this.guidanceMarkings = event.checked;
      console.log('Guidance Markings Toggle status:', event.checked);
    }
  }
}