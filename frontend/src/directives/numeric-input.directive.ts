import { Directive, ElementRef, HostListener, Output, EventEmitter } from '@angular/core';

/**
 * Directive that handles decimal separator conversion for numeric inputs.
 * 
 * Purpose: Firefox and some browsers accept comma as decimal separator in 
 * type="number" inputs, but store it as a string. This directive intercepts
 * input and converts comma to period before the value is processed.
 * 
 * Usage: Add `appNumericInput` to any numeric input element.
 * Example: <input type="number" appNumericInput [ngModel]="value" (ngModelChange)="value.set($event)">
 * 
 * Note: This directive does NOT implement ControlValueAccessor to avoid
 * conflicts with the existing ngModel signal-based bindings.
 */
@Directive({
  selector: 'input[type=number][appNumericInput]',
  standalone: true
})
export class NumericInputDirective {
  @Output() numericValueChange = new EventEmitter<number | null>();

  constructor(private el: ElementRef<HTMLInputElement>) {}

  @HostListener('keydown', ['$event'])
  onKeyDown(event: KeyboardEvent): void {
    const input = event.target as HTMLInputElement;
    const key = event.key;
    const ignoredKeys = [
      'Backspace', 'Delete', 'Tab', 'Enter', 'Escape', 
      'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'
    ];

    // Allow control keys and shortcuts (Ctrl+A, Ctrl+C, etc)
    if (ignoredKeys.includes(key) || event.ctrlKey || event.metaKey) {
      return;
    }

    // Allow numbers
    if (/[0-9]/.test(key)) {
      return;
    }

    // Allow decimal separator (dot or comma) if not present
    if (key === '.' || key === ',') {
      const currentVal = input.value;
      if (!currentVal.includes('.') && !currentVal.includes(',')) {
        return;
      }
    }

    // Prevent everything else
    event.preventDefault();
  }

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const rawValue = input.value;
    
    // Check if the value contains a comma (Firefox with Brazilian locale)
    if (rawValue.includes(',')) {
      // Replace comma with period
      const sanitized = rawValue.replace(',', '.');
      
      // Update the input element value
      input.value = sanitized;
      
      // Manually dispatch input event to trigger ngModel update
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
}
