import { DateInputComponent } from './date-input.component';

describe('DateInputComponent', () => {
  it('should create instance', () => {
    const component = new DateInputComponent();
    expect(component).toBeTruthy();
  });

  it('should emit value on change', () => {
    const component = new DateInputComponent();
    spyOn(component.ngModelChange, 'emit');
    component.onValueChange('2026-01-27');
    expect(component.ngModelChange.emit).toHaveBeenCalledWith('2026-01-27');
  });

  it('should handle empty date', () => {
    const component = new DateInputComponent();
    component.ngModel = '';
    expect(component.ngModel).toBe('');
  });

  it('should have default properties', () => {
    const component = new DateInputComponent();
    expect(component.label).toBe('');
    expect(component.placeholder).toBe('dd/mm/aaaa');
    expect(component.disabled).toBe(false);
    expect(component.required).toBe(false);
  });
});
