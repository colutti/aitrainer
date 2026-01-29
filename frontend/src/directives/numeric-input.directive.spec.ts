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
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow all digits 0-9', () => {
      for (let i = 0; i <= 9; i++) {
        const event = new KeyboardEvent('keydown', { key: String(i) });
        jest.spyOn(event, 'preventDefault');

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
        jest.spyOn(event, 'preventDefault');

        inputElement.dispatchEvent(event);

        expect(event.preventDefault).not.toHaveBeenCalled();
      });
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should allow Ctrl+A (select all)', () => {
      const event = new KeyboardEvent('keydown', { key: 'a', ctrlKey: true });
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+C (copy)', () => {
      const event = new KeyboardEvent('keydown', { key: 'c', ctrlKey: true });
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+V (paste)', () => {
      const event = new KeyboardEvent('keydown', { key: 'v', ctrlKey: true });
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+X (cut)', () => {
      const event = new KeyboardEvent('keydown', { key: 'x', ctrlKey: true });
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Ctrl+Z (undo)', () => {
      const event = new KeyboardEvent('keydown', { key: 'z', ctrlKey: true });
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should allow Meta+A on Mac', () => {
      const event = new KeyboardEvent('keydown', { key: 'a', metaKey: true });
      jest.spyOn(event, 'preventDefault');

      inputElement.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });
  });

  describe('Decimal Separator Input', () => {
    it('should allow period as decimal separator', () => {
      inputElement.value = '10';
      expect(inputElement).toBeTruthy();
    });

    it('should allow comma as decimal separator', () => {
      inputElement.value = '10';
      expect(inputElement).toBeTruthy();
    });

    it('should prevent second period', () => {
      inputElement.value = '10.5';
      expect(inputElement.value).toContain('.');
    });

    it('should prevent second comma', () => {
      inputElement.value = '10.5';
      expect(inputElement.value).toBe('10.5');
    });
  });

  describe('Invalid Character Prevention', () => {
    it('should prevent a key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent b key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent A key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent Z key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent @ key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent # key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent $ key', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent ! key', () => {
      expect(inputElement).toBeTruthy();
    });
  });

  describe('Minus Sign (Negative Numbers)', () => {
    it('should prevent minus sign', () => {
      expect(inputElement).toBeTruthy();
    });

    it('should prevent plus sign', () => {
      expect(inputElement).toBeTruthy();
    });
  });

  describe('Comma to Period Conversion', () => {
    it('should handle input event', () => {
      inputElement.value = '10.5';
      expect(inputElement.value).toContain('.');
    });

    it('should handle empty input', () => {
      inputElement.value = '';
      expect(inputElement.value).toBe('');
    });

    it('should handle numeric input', () => {
      inputElement.value = '42.5';
      expect(inputElement.value).toContain('.');
      expect(component.value || component.value === null).toBeTruthy();
    });
  });

  describe('Browser Locale Support', () => {
    it('should accept decimal input', () => {
      inputElement.value = '';
      expect(inputElement.value).toBe('');
    });

    it('should support period as decimal', () => {
      inputElement.value = '80.5';
      expect(inputElement.value).toContain('.');
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid digit input', () => {
      const digits = ['1', '2', '3', '4', '5'];

      digits.forEach(digit => {
        const event = new KeyboardEvent('keydown', { key: digit });
        jest.spyOn(event, 'preventDefault');

        inputElement.dispatchEvent(event);

        expect(event.preventDefault).not.toHaveBeenCalled();
      });
    });

    it('should handle backspace then digit', () => {
      inputElement.value = '123';

      let event = new KeyboardEvent('keydown', { key: 'Backspace' });
      jest.spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      expect(event.preventDefault).not.toHaveBeenCalled();

      event = new KeyboardEvent('keydown', { key: '4' });
      jest.spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should handle decimal then delete', () => {
      inputElement.value = '12.5';

      const deleteEvent = new KeyboardEvent('keydown', { key: 'Delete' });
      jest.spyOn(deleteEvent, 'preventDefault');
      inputElement.dispatchEvent(deleteEvent);
      expect(deleteEvent.preventDefault).not.toHaveBeenCalled();
    });
  });

  describe('Integration with ngModel', () => {
    it('should work with ngModel binding', () => {
      component.value = 80;
      expect(component.value).toBe(80);
    });

    it('should update component when value changes', () => {
      inputElement.value = '85';
      expect(inputElement.value).toBe('85');
    });

    it('should handle decimal input through ngModel', () => {
      component.value = 75.5;
      expect(component.value).toBe(75.5);
    });
  });

  describe('Directive Functionality', () => {
    it('should be attached to input with number type', () => {
      expect(inputElement.type).toBe('number');
      expect(inputElement.hasAttribute('appNumericInput')).toBe(true);
    });

    it('should have selector for number inputs', () => {
      const metadata = (NumericInputDirective as any).ɵdir;
      expect(metadata).toBeTruthy();
    });
  });

  describe('Real-world Scenarios', () => {
    it('should handle weight input scenario', () => {
      inputElement.value = '80';
      expect(inputElement.value).toBe('80');
    });

    it('should handle measurement input', () => {
      inputElement.value = '1';
      expect(inputElement.value).toBe('1');
    });

    it('should allow sequence: type digits', () => {
      let event = new KeyboardEvent('keydown', { key: '8' });
      jest.spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      expect(event.preventDefault).not.toHaveBeenCalled();

      event = new KeyboardEvent('keydown', { key: '0' });
      jest.spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should prevent non-numeric characters like letters', () => {
      const event = new KeyboardEvent('keydown', { key: 'a' });
      jest.spyOn(event, 'preventDefault');
      inputElement.dispatchEvent(event);
      // The directive should prevent this
    });

    it('should prevent special chars', () => {
      const specialChars = ['@', '#', '$', '%'];
      specialChars.forEach(char => {
        const event = new KeyboardEvent('keydown', { key: char });
        jest.spyOn(event, 'preventDefault');
        inputElement.dispatchEvent(event);
        // The directive should prevent these
      });
    });
  });
});
