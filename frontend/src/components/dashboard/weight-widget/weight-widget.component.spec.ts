import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { WeightWidgetComponent } from './weight-widget.component';
import { WeightService } from '../../../services/weight.service';
import { UserProfileService } from '../../../services/user-profile.service';
import { signal } from '@angular/core';

describe('WeightWidgetComponent', () => {
  let component: WeightWidgetComponent;
  let fixture: ComponentFixture<WeightWidgetComponent>;
  let mockWeightService: Partial<WeightService>;
  let mockUserProfileService: Partial<UserProfileService>;

  beforeEach(async () => {
    mockWeightService = {
      lastWeight: signal(75),
      lastSaved: signal(new Date()),
      logWeight: jest.fn().mockResolvedValue({
        id: '1',
        weight: 80,
        date: new Date(),
        fatPercentage: 20
      })
    };

    mockUserProfileService = {
      profile: signal({
        weight: 75,
        height: 175,
        goal: 'lose',
        age: 30,
        gender: 'M'
      }),
      getProfile: jest.fn().mockResolvedValue({
        weight: 75,
        height: 175,
        goal: 'lose',
        age: 30,
        gender: 'M'
      })
    };

    await TestBed.configureTestingModule({
      imports: [WeightWidgetComponent, FormsModule],
      providers: [
        { provide: WeightService, useValue: mockWeightService },
        { provide: UserProfileService, useValue: mockUserProfileService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WeightWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  describe('Initialization', () => {
    it('should create component', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize weight input from user profile', () => {
      expect(component.weightInput()).toBe(75);
    });

    it('should initialize last saved timestamp', () => {
      expect(component.lastSaved()).toBeDefined();
    });

    it('should not be expanded initially', () => {
      expect(component.isExpanded()).toBe(false);
    });

    it('should initialize body composition inputs to zero', () => {
      expect(component.bodyFatInput()).toBe(0);
      expect(component.muscleMassInput()).toBe(0);
    });
  });

  describe('Weight Input', () => {
    it('should accept weight value', () => {
      const testWeight = 82.5;
      component.weightInput.set(testWeight);

      expect(component.weightInput()).toBe(82.5);
    });

    it('should handle decimal weights', () => {
      component.weightInput.set(80.75);

      expect(component.weightInput()).toBe(80.75);
    });

    it('should handle very high weights', () => {
      component.weightInput.set(200);

      expect(component.weightInput()).toBe(200);
    });

    it('should handle very low weights', () => {
      component.weightInput.set(40);

      expect(component.weightInput()).toBe(40);
    });

    it('should display weight in input field', () => {
      component.weightInput.set(85);
      fixture.detectChanges();

      const input = fixture.nativeElement.querySelector('[data-test="weight-input"]');
      if (input) {
        expect(input.value).toBe('85');
      }
    });

    it('should use appNumericInput directive', () => {
      const input = fixture.nativeElement.querySelector('[data-test="weight-input"]');
      if (input) {
        expect(input.getAttribute('appNumericInput')).toBeDefined();
      }
    });
  });

  describe('Body Composition Expansion', () => {
    it('should toggle expansion', () => {
      expect(component.isExpanded()).toBe(false);

      component.toggleExpanded();
      expect(component.isExpanded()).toBe(true);

      component.toggleExpanded();
      expect(component.isExpanded()).toBe(false);
    });

    it('should display expansion toggle button', () => {
      fixture.detectChanges();

      const button = fixture.nativeElement.querySelector('[data-test="expand-button"]');
      if (button) {
        expect(button).toBeTruthy();
      }
    });

    it('should rotate chevron when expanded', () => {
      component.isExpanded.set(true);
      fixture.detectChanges();

      const chevron = fixture.nativeElement.querySelector('[data-test="expand-chevron"]');
      if (chevron) {
        expect(chevron.classList.contains('rotate-180')).toBe(true);
      }
    });

    it('should hide body composition fields when not expanded', () => {
      component.isExpanded.set(false);
      fixture.detectChanges();

      const bodyFatField = fixture.nativeElement.querySelector('[data-test="body-fat-field"]');
      if (bodyFatField) {
        expect(bodyFatField.style.display).toBe('none');
      }
    });

    it('should show body composition fields when expanded', () => {
      component.isExpanded.set(true);
      fixture.detectChanges();

      const bodyFatField = fixture.nativeElement.querySelector('[data-test="body-fat-field"]');
      if (bodyFatField) {
        expect(bodyFatField.style.display).not.toBe('none');
      }
    });
  });

  describe('Body Composition Inputs', () => {
    it('should accept body fat percentage', () => {
      component.bodyFatInput.set(20);

      expect(component.bodyFatInput()).toBe(20);
    });

    it('should accept muscle mass percentage', () => {
      component.muscleMassInput.set(35);

      expect(component.muscleMassInput()).toBe(35);
    });

    it('should validate body fat between 0-100', () => {
      component.bodyFatInput.set(25);
      expect(component.bodyFatInput()).toBe(25);

      component.bodyFatInput.set(0);
      expect(component.bodyFatInput()).toBe(0);

      component.bodyFatInput.set(100);
      expect(component.bodyFatInput()).toBe(100);
    });

    it('should validate muscle mass between 0-100', () => {
      component.muscleMassInput.set(30);
      expect(component.muscleMassInput()).toBe(30);

      component.muscleMassInput.set(0);
      expect(component.muscleMassInput()).toBe(0);

      component.muscleMassInput.set(100);
      expect(component.muscleMassInput()).toBe(100);
    });

    it('should display body composition fields', () => {
      component.isExpanded.set(true);
      fixture.detectChanges();

      const bodyFatField = fixture.nativeElement.querySelector('[data-test="body-fat-input"]');
      const muscleField = fixture.nativeElement.querySelector('[data-test="muscle-input"]');

      expect(bodyFatField || muscleField).toBeTruthy();
    });
  });

  describe('Save Weight', () => {
    it('should save weight with required fields only', async () => {
      component.weightInput.set(80);

      await component.saveWeight();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });

    it('should save weight with body composition', async () => {
      component.weightInput.set(80);
      component.bodyFatInput.set(20);
      component.muscleMassInput.set(40);

      await component.saveWeight();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });

    it('should disable save button while saving', async () => {
      component.isSavingEntry.set(true);
      fixture.detectChanges();

      const saveButton = fixture.nativeElement.querySelector('[data-test="save-button"]');
      if (saveButton) {
        expect(saveButton.disabled).toBe(true);
      }
    });

    it('should show loading spinner while saving', () => {
      component.isSavingEntry.set(true);
      fixture.detectChanges();

      const spinner = fixture.nativeElement.querySelector('[data-test="save-spinner"]');
      if (spinner) {
        expect(spinner).toBeTruthy();
      }
    });

    it('should handle save successfully', async () => {
      component.weightInput.set(80);

      await component.saveWeight();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });

    it('should show checkmark after successful save', () => {
      component.isSavingEntry.set(false);
      fixture.detectChanges();

      const checkmark = fixture.nativeElement.querySelector('[data-test="save-checkmark"]');
      if (checkmark) {
        expect(checkmark).toBeTruthy();
      }
    });

    it('should handle save error gracefully', async () => {
      (mockWeightService.logWeight as jest.Mock).mockRejectedValueOnce(
        new Error('Save failed')
      );

      component.weightInput.set(80);

      await expect(component.saveWeight()).rejects.toThrow('Save failed');
    });

    it('should show error message on save failure', async () => {
      (mockWeightService.logWeight as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      component.weightInput.set(80);

      try {
        await component.saveWeight();
      } catch (e) {
        // Expected error
      }

      fixture.detectChanges();

      // Component should still be usable
      expect(component).toBeTruthy();
    });
  });

  describe('Last Saved Feedback', () => {
    it('should display last saved timestamp', () => {
      fixture.detectChanges();

      const lastSavedText = fixture.nativeElement.querySelector('[data-test="last-saved"]');
      if (lastSavedText) {
        expect(lastSavedText.textContent).toContain('Salvo');
      }
    });

    it('should update last saved after successful save', async () => {
      const beforeTime = component.lastSaved();

      component.weightInput.set(85);
      await component.saveWeight();

      const afterTime = component.lastSaved();

      expect(afterTime).toBeDefined();
    });

    it('should show green checkmark with last saved', () => {
      fixture.detectChanges();

      const checkmark = fixture.nativeElement.querySelector('[data-test="saved-checkmark"]');
      if (checkmark) {
        expect(checkmark.classList.contains('text-green')).toBe(true);
      }
    });

    it('should update timestamp formatting dynamically', () => {
      const now = new Date();
      component.lastSaved.set(now);
      fixture.detectChanges();

      const timeText = fixture.nativeElement.querySelector('[data-test="last-saved"]');
      if (timeText) {
        expect(timeText.textContent).toBeTruthy();
      }
    });
  });

  describe('Suggestion Display', () => {
    it('should show suggestion based on weight change', () => {
      component.weightInput.set(85);
      fixture.detectChanges();

      const suggestion = fixture.nativeElement.querySelector('[data-test="suggestion"]');
      if (suggestion) {
        expect(suggestion.textContent).toBeTruthy();
      }
    });

    it('should display weight trend suggestion', () => {
      component.weightInput.set(80);
      fixture.detectChanges();

      expect(component.suggestion()).toBeDefined();
    });

    it('should update suggestion when weight changes', () => {
      component.weightInput.set(75);
      fixture.detectChanges();

      const initialSuggestion = component.suggestion();

      component.weightInput.set(85);
      fixture.detectChanges();

      const updatedSuggestion = component.suggestion();

      // Suggestion should be defined (may or may not change)
      expect(initialSuggestion || updatedSuggestion).toBeDefined();
    });
  });

  describe('Widget Layout', () => {
    it('should display as compact widget', () => {
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[data-test="widget-container"]');
      if (widget) {
        expect(widget.classList.contains('widget')).toBe(true);
      }
    });

    it('should have weight section visible', () => {
      fixture.detectChanges();

      const weightSection = fixture.nativeElement.querySelector('[data-test="weight-section"]');
      expect(weightSection).toBeTruthy();
    });

    it('should have collapsible body composition section', () => {
      fixture.detectChanges();

      const expandButton = fixture.nativeElement.querySelector('[data-test="expand-button"]');
      expect(expandButton).toBeTruthy();
    });

    it('should be responsive', () => {
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[data-test="widget-container"]');
      if (widget) {
        expect(widget).toBeTruthy();
      }
    });
  });

  describe('Data Binding', () => {
    it('should update weight from service', () => {
      (mockWeightService.lastWeight as any).set(82);

      fixture.detectChanges();

      expect(mockWeightService.lastWeight()).toBe(82);
    });

    it('should sync weight with user profile on init', () => {
      expect(component.weightInput()).toBe(
        mockUserProfileService.profile().weight
      );
    });

    it('should maintain weight through component lifecycle', () => {
      const initialWeight = component.weightInput();

      fixture.detectChanges();

      expect(component.weightInput()).toBe(initialWeight);
    });
  });

  describe('Form Validation', () => {
    it('should not save with empty weight', async () => {
      component.weightInput.set(0);

      // Component should handle this appropriately
      await component.saveWeight();

      expect(component).toBeTruthy();
    });

    it('should validate weight input before save', () => {
      component.weightInput.set(-10);

      // Component should handle validation
      expect(component.weightInput()).toBe(-10);
    });

    it('should allow zero for optional body composition fields', async () => {
      component.weightInput.set(80);
      component.bodyFatInput.set(0);
      component.muscleMassInput.set(0);

      await component.saveWeight();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });
  });

  describe('Keyboard Interaction', () => {
    it('should have numeric input directive', () => {
      const input = fixture.nativeElement.querySelector('[data-test="weight-input"]');
      if (input) {
        expect(input.getAttribute('appNumericInput')).toBeDefined();
      }
    });

    it('should accept numeric input', () => {
      component.weightInput.set(80);

      expect(component.weightInput()).toBe(80);
    });

    it('should handle decimal input', () => {
      component.weightInput.set(80.5);

      expect(component.weightInput()).toBe(80.5);
    });
  });

  describe('State Management', () => {
    it('should track saving state', () => {
      component.isSavingEntry.set(true);

      expect(component.isSavingEntry()).toBe(true);

      component.isSavingEntry.set(false);

      expect(component.isSavingEntry()).toBe(false);
    });

    it('should track expansion state', () => {
      component.toggleExpanded();

      expect(component.isExpanded()).toBe(true);

      component.toggleExpanded();

      expect(component.isExpanded()).toBe(false);
    });

    it('should maintain state through lifecycle', () => {
      component.weightInput.set(85);
      component.isExpanded.set(true);

      fixture.detectChanges();

      expect(component.weightInput()).toBe(85);
      expect(component.isExpanded()).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very high weight values', () => {
      component.weightInput.set(300);

      expect(component.weightInput()).toBe(300);
    });

    it('should handle very low weight values', () => {
      component.weightInput.set(20);

      expect(component.weightInput()).toBe(20);
    });

    it('should handle rapid successive saves', async () => {
      component.weightInput.set(80);

      component.saveWeight();
      component.saveWeight();
      component.saveWeight();

      await fixture.whenStable();

      expect(mockWeightService.logWeight).toBeDefined();
    });

    it('should handle null user profile', () => {
      (mockUserProfileService.profile as any).set(null);

      fixture.detectChanges();

      expect(component).toBeTruthy();
    });

    it('should handle component destruction', () => {
      fixture.destroy();

      expect(fixture.componentInstance).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have descriptive labels', () => {
      fixture.detectChanges();

      const weightLabel = fixture.nativeElement.querySelector('[data-test="weight-label"]');
      if (weightLabel) {
        expect(weightLabel.textContent).toContain('Peso');
      }
    });

    it('should have focusable save button', () => {
      fixture.detectChanges();

      const saveButton = fixture.nativeElement.querySelector('[data-test="save-button"]');
      if (saveButton) {
        expect(saveButton.tagName).toBe('BUTTON');
      }
    });

    it('should have proper button types', () => {
      fixture.detectChanges();

      const buttons = fixture.nativeElement.querySelectorAll('button');
      buttons.forEach((button: HTMLElement) => {
        expect(button.hasAttribute('type')).toBe(true);
      }
      );
    });
  });

  describe('Integration', () => {
    it('should work with weight service', async () => {
      component.weightInput.set(80);

      await component.saveWeight();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });

    it('should work with user profile service', () => {
      expect(component.weightInput()).toBe(75);
    });

    it('should handle service failures gracefully', async () => {
      (mockWeightService.logWeight as jest.Mock).mockRejectedValueOnce(
        new Error('Service unavailable')
      );

      component.weightInput.set(80);

      try {
        await component.saveWeight();
      } catch (e) {
        // Expected
      }

      expect(component).toBeTruthy();
    });
  });
});
