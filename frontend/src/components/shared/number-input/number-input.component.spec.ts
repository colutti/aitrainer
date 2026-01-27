import { NumberInputComponent } from './number-input.component';

describe('NumberInputComponent', () => {
  it('should create instance', () => {
    const component = new NumberInputComponent();
    expect(component).toBeTruthy();
  });

  it('should emit value on change', () => {
    const component = new NumberInputComponent();
    spyOn(component.ngModelChange, 'emit');
    component.onValueChange(72.5);
    expect(component.ngModelChange.emit).toHaveBeenCalledWith(72.5);
  });

  it('should handle null value', () => {
    const component = new NumberInputComponent();
    spyOn(component.ngModelChange, 'emit');
    component.onValueChange(null);
    expect(component.ngModelChange.emit).toHaveBeenCalledWith(null);
  });

  it('should have default properties', () => {
    const component = new NumberInputComponent();
    expect(component.label).toBe('');
    expect(component.placeholder).toBe('0.0');
    expect(component.step).toBe(0.1);
    expect(component.disabled).toBe(false);
  });
});
