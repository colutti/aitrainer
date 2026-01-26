import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-container',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg rounded-2xl border border-secondary shadow-lg
                hover:border-primary/50 transition-colors duration-300 p-4 flex flex-col"
         [class.h-24]="size === 'sm'"
         [class.h-40]="size === 'md'"
         [class.h-60]="size === 'lg'">
      <ng-content></ng-content>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetContainerComponent {
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
}
