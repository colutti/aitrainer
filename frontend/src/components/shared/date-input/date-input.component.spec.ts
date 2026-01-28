import { TestBed, ComponentFixture } from '@angular/core/testing';
import { DateInputComponent } from './date-input.component';
import { FormsModule } from '@angular/forms';

describe('DateInputComponent', () => {
  let component: DateInputComponent;
  let fixture: ComponentFixture<DateInputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DateInputComponent, FormsModule],
      declarations: []
    }).compileComponents();

    fixture = TestBed.createComponent(DateInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create instance', () => {
    expect(component).toBeTruthy();
  });

  it('should emit value on change', () => {
    spyOn(component.ngModelChange, 'emit');
    component.onValueChange('2026-01-27');
    expect(component.ngModelChange.emit).toHaveBeenCalledWith('2026-01-27');
  });

  it('should handle empty date', () => {
    component.ngModel = '';
    expect(component.ngModel).toBe('');
  });

  it('should have default properties', () => {
    expect(component.label).toBe('');
    expect(component.placeholder).toBe('dd/mm/aaaa');
    expect(component.disabled).toBe(false);
    expect(component.required).toBe(false);
  });
});
