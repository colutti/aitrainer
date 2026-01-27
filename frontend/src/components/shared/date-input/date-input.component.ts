import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgbModule, NgbDateStruct } from '@ng-bootstrap/ng-bootstrap';

/**
 * Reusable date input component with ng-bootstrap datepicker
 * Supports two-way binding with [(ngModel)]
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
  imports: [CommonModule, FormsModule, NgbModule],
  templateUrl: './date-input.component.html',
  styleUrls: ['./date-input.component.css']
})
export class DateInputComponent {
  @Input() label: string = '';
  @Input() placeholder: string = 'dd/mm/aaaa';
  @Input() disabled: boolean = false;
  @Input() required: boolean = false;
  @Input() minDate?: NgbDateStruct;
  @Input() maxDate?: NgbDateStruct;

  // ngModel support
  @Input() ngModel: string = '';
  @Output() ngModelChange = new EventEmitter<string>();

  /**
   * Convert ISO date string (YYYY-MM-DD) to NgbDateStruct
   */
  get dateStruct(): NgbDateStruct | null {
    if (!this.ngModel) return null;

    try {
      const [year, month, day] = this.ngModel.split('-').map(Number);
      return { year, month, day };
    } catch {
      return null;
    }
  }

  /**
   * Handle date selection from datepicker
   */
  onDateChange(date: NgbDateStruct | null): void {
    if (date) {
      const isoDate = `${date.year}-${String(date.month).padStart(2, '0')}-${String(date.day).padStart(2, '0')}`;
      this.ngModel = isoDate;
      this.ngModelChange.emit(isoDate);
    }
  }
}
