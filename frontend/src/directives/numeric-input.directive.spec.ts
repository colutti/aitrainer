import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NumericInputDirective } from './numeric-input.directive';

@Component({
  template: `<input type="number" appNumericInput [(ngModel)]="value" />`
})
class TestComponent {
  value: number | null = null;
}

describe('NumericInputDirective', () => {
  let component: TestComponent;
  let fixture: ComponentFixture<TestComponent>;
  let inputElement: HTMLInputElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NumericInputDirective, FormsModule, TestComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    component = fixture.componentInstance;
    inputElement = fixture.nativeElement.querySelector('input');
    fixture.detectChanges();
  });

  describe('Directive Creation', () => {
    it('should create directive', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should apply to input[type=number]', () => {
      expect(inputElement.type).toBe('number');
    });

    it('should be standalone', () => {
      const metadata = (NumericInputDirective as any).ɵdir;
      expect(metadata.standalone).toBe(true);
    });
  });

  describe('Numeric Input Acceptance', () => {
    it('should allow digits', () => {
      const event = new KeyboardEvent('keydown', { key: '5' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow all digits 0-9', () => {
      for (let i = 0; i <= 9; i++) {
        const event = new KeyboardEvent('keydown', { key: String(i) });
        spyOn(event, 'preventDefault');

        inputElement.dispatchEvent(event);

        expect(event.preventDefault).not.toHaveBeenCalled();
      }
    });
  });

  describe('Control Keys', () => {
    const controlKeys = [
      'Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
      'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'
    ];

    controlKeys.forEach(key => {
      it(`should allow ${key} key`, () => {
        const event = new KeyboardEvent('keydown', { key });
        spyOn(event, 'preventDefault');

        inputElement.dispatchEvent(event);

        expect(event.preventDefault).not.toHaveBeenCalled();
      });
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should allow Ctrl+A (select all)', () => {
      const event = new KeyboardEvent('keydown', { key: 'a', ctrlKey: true });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+C (copy)', () => {
      const event = new KeyboardEvent('keydown', { key: 'c', ctrlKey: true });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+V (paste)', () => {
      const event = new KeyboardEvent('keydown', { key: 'v', ctrlKey: true });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+X (cut)', () => {
      const event = new KeyboardEvent('keydown', { key: 'x', ctrlKey: true });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+Z (undo)', () => {
      const event = new KeyboardEvent('keydown', { key: 'z', ctrlKey: true });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Meta+A on Mac', () => {
      const event = new KeyboardEvent('keydown', { key: 'a', metaKey: true });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });
  });

  describe('Decimal Separator Input', () => {
    it('should allow period as decimal separator', () => {
      inputElement.value = '10';

      const event = new KeyboardEvent('keydown', { key: '.' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow comma as decimal separator', () => {
      inputElement.value = '10';

      const event = new KeyboardEvent('keydown', { key: ',' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should prevent second period', () => {
      inputElement.value = '10.5';

      const event = new KeyboardEvent('keydown', { key: '.' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should prevent second comma', () => {
      inputElement.value = '10,5';

      const event = new KeyboardEvent('keydown', { key: ',' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should prevent period when comma already exists', () => {
      inputElement.value = '10,5';

      const event = new KeyboardEvent('keydown', { key: '.' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should prevent comma when period already exists', () => {
      inputElement.value = '10.5';

      const event = new KeyboardEvent('keydown', { key: ',' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });
  });

  describe('Invalid Character Prevention', () => {
    const invalidChars = ['a', 'b', 'A', 'Z', '@', '#', '$', '!', ' '];

    invalidChars.forEach(char => {
      it(`should prevent ${char} key`, () => {
        const event = new KeyboardEvent('keydown', { key: char });
        spyOn(event, 'preventDefault');

        inputElement.dispatchEvent(event);

        expect(event.preventDefault).toHaveBeenCalled();
      });
    });
  });

  describe('Minus Sign (Negative Numbers)', () => {
    it('should prevent minus sign', () => {
      const event = new KeyboardEvent('keydown', { key: '-' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should prevent plus sign', () => {
      const event = new KeyboardEvent('keydown', { key: '+' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });
  });

  describe('Comma to Period Conversion', () => {
    it('should convert comma to period on input', () => {
      inputElement.value = '10,5';

      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe('10.5');
    });

    it('should handle multiple comma entries', () => {
      inputElement.value = '10,5';

      // First conversion
      let inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe('10.5');

      // Try to add comma again (should be prevented by keydown)
      const keyEvent = new KeyboardEvent('keydown', { key: ',' });
      spyOn(keyEvent, 'preventDefault');
      inputElement.dispatchEvent(keyEvent);

      expect(keyEvent.preventDefault).toHaveBeenCalled();
    });

    it('should re-dispatch input event after conversion', () => {
      inputElement.value = '10,5';

      const inputSpy = spyOn(inputElement, 'dispatchEvent').and.callThrough();

      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      // Should have dispatched event again after conversion
      expect(inputSpy).toHaveBeenCalledTimes(2);
    });

    it('should not trigger conversion if no comma present', () => {
      inputElement.value = '10.5';

      const initialValue = inputElement.value;
      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe(initialValue);
    });

    it('should handle empty input', () => {
      inputElement.value = '';

      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe('');
    });

    it('should handle just comma', () => {
      inputElement.value = ',';

      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe('.');
    });
  });

  describe('Browser Locale Support', () => {
    it('should accept comma for Firefox with Brazilian locale', () => {
      inputElement.value = '';

      const event = new KeyboardEvent('keydown', { key: ',' });
      spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      // Should be allowed if no separator yet
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should convert comma to period for internal processing', () => {
      inputElement.value = '80,5';

      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe('80.5');
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid digit input', () => {
      const digits = ['1', '2', '3', '4', '5'];

      digits.forEach(digit => {
        const event = new KeyboardEvent('keydown', { key: digit });
        spyOn(event, 'preventDefault');

        inputElement.dispatchEvent(event);

        expect(event.preventDefault).not.toHaveBeenCalled();
      });
    });

    it('should handle backspace then digit', () => {
      inputElement.value = '123';

      let event = new KeyboardEvent('keydown', { key: 'Backspace' });
      spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      expect(event.preventDefault).not.toHaveBeenCalled();

      event = new KeyboardEvent('keydown', { key: '4' });
      spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should handle decimal then delete', () => {
      inputElement.value = '12.5';

      const deleteEvent = new KeyboardEvent('keydown', { key: 'Delete' });
      spyOn(deleteEvent, 'preventDefault');
      inputElement.dispatchEvent(deleteEvent);
      expect(deleteEvent.preventDefault).not.toHaveBeenCalled();
    });

    it('should maintain value through multiple conversions', () => {
      inputElement.value = '42,5';
      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();

      expect(inputElement.value).toBe('42.5');
      expect(component.value).toBeTruthy();
    });
  });

  describe('Integration with ngModel', () => {
    it('should work with ngModel binding', async () => {
      component.value = 80;
      fixture.detectChanges();
      await fixture.whenStable();

      expect(inputElement.value).toBe('80');
    });

    it('should update component when value changes', async () => {
      inputElement.value = '85';
      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.value).toBeTruthy();
    });

    it('should handle decimal input through ngModel', async () => {
      component.value = 75.5;
      fixture.detectChanges();
      await fixture.whenStable();

      expect(inputElement.value).toBeTruthy();
    });
  });
});
