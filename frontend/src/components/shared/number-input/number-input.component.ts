import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NumericInputDirective } from '../../../directives/numeric-input.directive';

/**
 * Reusable number input component with built-in numeric directive
 * Supports two-way binding with [(ngModel)]
 * Automatically handles comma-to-period conversion
 *
 * Usage:
 * <app-number-input
 *   label="Peso"
 *   unit="kg"
 *   [ngModel]="weight()"
 *   (ngModelChange)="weight.set($event)"
 *   [min]="30"
 *   [max]="500"
 *   [step]="0.1">
 * </app-number-input>
 */
@Component({
  selector: 'app-number-input',
  standalone: true,
  imports: [CommonModule, FormsModule, NumericInputDirective], // NumericInputDirective é usado no template via appNumericInput
  templateUrl: './number-input.component.html',
  styleUrls: ['./number-input.component.css']
})
export class NumberInputComponent {
  @Input() label: string = '';
  @Input() placeholder: string = '0.0';
  @Input() min?: number;
  @Input() max?: number;
  @Input() step: number = 0.1;
  @Input() disabled: boolean = false;
  @Input() required: boolean = false;
  @Input() unit: string = ''; // 'kg', '%', 'cm', etc.
  @Input() dataCy?: string; // For E2E testing

  // ngModel support
  @Input() ngModel: number | null = null;
  @Output() ngModelChange = new EventEmitter<number | null>();

  /**
   * Handle value change from input
   */
  onValueChange(value: number | null): void {
    this.ngModel = value;
    this.ngModelChange.emit(value);
  }
}
