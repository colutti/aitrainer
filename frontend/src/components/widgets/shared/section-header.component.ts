import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-section-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="col-span-full flex items-center gap-4 mt-6 mb-4">
      <div>
        <h2 class="text-lg font-bold text-white">{{ title }}</h2>
        <p class="text-xs text-text-secondary opacity-60">{{ subtitle }}</p>
      </div>
      <div class="flex-1 h-px bg-secondary/30"></div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SectionHeaderComponent {
  @Input() title: string = '';
  @Input() subtitle: string = '';
}
