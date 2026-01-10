import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="animate-pulse bg-gray-700/50 rounded"
      [style.width]="width"
      [style.height]="height"
      [ngClass]="{
        'rounded-full': shape === 'circle',
        'rounded-md': shape === 'rect'
      }"
    ></div>
  `
})
export class SkeletonComponent {
  @Input() width = '100%';
  @Input() height = '1rem';
  @Input() shape: 'rect' | 'circle' = 'rect';
}
