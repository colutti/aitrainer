import { Pipe, PipeTransform } from '@angular/core';
import { DatePipe } from '@angular/common';

/**
 * Custom date formatting pipe with preset Brazilian formats
 * Usage: {{ date | appDateFormat:'medium' }}
 *
 * Available formats:
 * - 'short': dd/MM/yy
 * - 'medium': dd/MM/yyyy (default)
 * - 'long': dd MMM yyyy
 * - 'time': HH:mm
 * - 'datetime': dd MMM yyyy • HH:mm
 * - 'shortMonth': dd MMM
 * - 'dayMonth': dd/MM
 * - 'full': dd/MM/yyyy HH:mm
 */
@Pipe({
  name: 'appDateFormat',
  standalone: true
})
export class AppDateFormatPipe implements PipeTransform {
  private datePipe = new DatePipe('pt-BR');

  private formats: Record<string, string> = {
    short: 'dd/MM/yy',
    medium: 'dd/MM/yyyy',
    long: 'dd MMM yyyy',
    time: 'HH:mm',
    datetime: 'dd MMM yyyy • HH:mm',
    shortMonth: 'dd MMM',
    dayMonth: 'dd/MM',
    full: 'dd/MM/yyyy HH:mm'
  };

  transform(value: any, format: string = 'medium'): string | null {
    return this.datePipe.transform(value, this.formats[format] || format);
  }
}
