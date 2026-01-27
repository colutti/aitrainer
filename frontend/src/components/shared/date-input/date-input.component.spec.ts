import { DateInputComponent } from './date-input.component';

describe('DateInputComponent', () => {
  it('should create instance', () => {
    const component = new DateInputComponent();
    expect(component).toBeTruthy();
  });

  it('should convert ISO date string to NgbDateStruct', () => {
    const component = new DateInputComponent();
    component.ngModel = '2026-01-27';
    const dateStruct = component.dateStruct;
    expect(dateStruct).toEqual({ year: 2026, month: 1, day: 27 });
  });

  it('should handle null date', () => {
    const component = new DateInputComponent();
    component.ngModel = '';
    expect(component.dateStruct).toBeNull();
  });
});
