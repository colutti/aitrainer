import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

/**
 * Simple date input wrapper around HTML5 native input type="date"
 * - No external dependencies (ng-bootstrap removed for stability)
 * - Works with ISO format (YYYY-MM-DD) for backend compatibility
 * - Browser handles locale formatting automatically
 * - Much lighter and more reliable
 *
 * Usage:
 * <app-date-input
 *   label="Data de Nascimento"
 *   [ngModel]="dateValue()"
 *   (ngModelChange)="dateValue.set($event)"
 *   [required]="true">
 * </app-date-input>
 */
@Component({
  selector: 'app-date-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './date-input.component.html',
  styleUrls: ['./date-input.component.css']
})
export class DateInputComponent {
  @Input() label: string = '';
  @Input() placeholder: string = 'dd/mm/aaaa';
  @Input() disabled: boolean = false;
  @Input() required: boolean = false;
  @Input() min?: string; // ISO format YYYY-MM-DD
  @Input() max?: string; // ISO format YYYY-MM-DD

  // ngModel support
  @Input() ngModel: string = '';
  @Output() ngModelChange = new EventEmitter<string>();

  /**
   * Handle date value changes
   */
  onValueChange(value: string): void {
    this.ngModel = value;
    this.ngModelChange.emit(value);
  }
}
