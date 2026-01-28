import { TestBed, ComponentFixture } from '@angular/core/testing';
import { NumberInputComponent } from './number-input.component';
import { FormsModule } from '@angular/forms';

describe('NumberInputComponent', () => {
  let component: NumberInputComponent;
  let fixture: ComponentFixture<NumberInputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NumberInputComponent, FormsModule],
      declarations: []
    }).compileComponents();

    fixture = TestBed.createComponent(NumberInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create instance', () => {
    expect(component).toBeTruthy();
  });

  it('should emit value on change', () => {
    spyOn(component.ngModelChange, 'emit');
    component.onValueChange(72.5);
    expect(component.ngModelChange.emit).toHaveBeenCalledWith(72.5);
  });

  it('should handle null value', () => {
    spyOn(component.ngModelChange, 'emit');
    component.onValueChange(null);
    expect(component.ngModelChange.emit).toHaveBeenCalledWith(null);
  });

  it('should have default properties', () => {
    expect(component.label).toBe('');
    expect(component.placeholder).toBe('0.0');
    expect(component.step).toBe(0.1);
    expect(component.disabled).toBe(false);
  });
});
