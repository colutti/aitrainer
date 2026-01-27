import { Pipe, PipeTransform } from '@angular/core';
import { DecimalPipe } from '@angular/common';

/**
 * Custom number formatting pipe with preset formats
 * Usage: {{ value | appNumberFormat:'weight' }}
 *
 * Available formats:
 * - 'integer': 1.0-0 (whole numbers)
 * - 'decimal1': 1.1-1 (one decimal place)
 * - 'decimal2': 1.2-2 (two decimal places)
 * - 'weight': 1.1-1 (alias for decimal1)
 * - 'percentage': 1.2-2 (alias for decimal2)
 */
@Pipe({
  name: 'appNumberFormat',
  standalone: true
})
export class AppNumberFormatPipe implements PipeTransform {
  private decimalPipe = new DecimalPipe('pt-BR');

  private formats: Record<string, string> = {
    integer: '1.0-0',
    decimal1: '1.1-1',
    decimal2: '1.2-2',
    weight: '1.1-1',
    percentage: '1.2-2'
  };

  transform(value: any, format: string = 'decimal1'): string | null {
    return this.decimalPipe.transform(value, this.formats[format] || format);
  }
}
