import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UserProfileComponent } from './user-profile.component';
import { UserProfileService } from '../../services/user-profile.service';
import { UserProfile } from '../../models/user-profile.model';
import { UserProfileInput } from '../../models/user-profile-input.model';

describe('UserProfileComponent', () => {
  let component: UserProfileComponent;
  let fixture: ComponentFixture<UserProfileComponent>;
  let userProfileServiceMock: Partial<UserProfileService>;

  const mockProfile: UserProfile = {
    gender: 'male',
    age: 30,
    weight: 80,
    height: 180,
    goal: 'lose weight',
    goal_type: 'deficit',
    weekly_rate: -0.5,
    target_weight: 75,
    email: 'test@test.com',
    notes: 'Some notes'
  };

  beforeEach(async () => {
    userProfileServiceMock = {
      getProfile: jest.fn().mockResolvedValue(mockProfile),
      updateProfile: jest.fn().mockResolvedValue(mockProfile)
    };

    await TestBed.configureTestingModule({
      imports: [UserProfileComponent],
      providers: [
        { provide: UserProfileService, useValue: userProfileServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UserProfileComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should load profile on init', async () => {
      await component.ngOnInit();

      expect(userProfileServiceMock.getProfile).toHaveBeenCalled();
      expect(component.profile().email).toBe('test@test.com');
    });

    it('should initialize with default values', () => {
      expect(component.profile()).toBeDefined();
      expect(component.isSaving()).toBe(false);
      expect(component.showSuccess()).toBe(false);
      expect(component.validationErrors()).toEqual({});
    });

    it('should handle missing profile gracefully', async () => {
      (userProfileServiceMock.getProfile as jest.Mock).mockResolvedValueOnce(null);

      await component.ngOnInit();

      // Should keep default values
      expect(component.profile()).toBeDefined();
    });
  });

  describe('Goal Type Change', () => {
    beforeEach(async () => {
      await component.ngOnInit();
    });

    it('should clear weekly_rate when changing to maintain', () => {
      const profile = component.profile();
      component.profile.set({ ...profile, weekly_rate: -0.5 });

      component.onGoalTypeChange();
      // Note: component should track goal_type change separately in real usage

      // For this test, manually set to maintain
      component.profile.update(p => ({ ...p, goal_type: 'maintain' }));
      component.onGoalTypeChange();

      expect(component.profile().weekly_rate).toBe(0);
    });

    it('should keep weekly_rate for deficit goal', () => {
      component.profile.set({
        ...component.profile(),
        goal_type: 'deficit',
        weekly_rate: -0.5
      });

      component.onGoalTypeChange();

      expect(component.profile().weekly_rate).toBe(-0.5);
    });

    it('should keep weekly_rate for surplus goal', () => {
      component.profile.set({
        ...component.profile(),
        goal_type: 'surplus',
        weekly_rate: 0.5
      });

      component.onGoalTypeChange();

      expect(component.profile().weekly_rate).toBe(0.5);
    });
  });

  describe('Save Profile', () => {
    beforeEach(async () => {
      await component.ngOnInit();
    });

    it('should save profile successfully', async () => {
      component.profile.set({
        ...component.profile(),
        weight: 75
      });

      await component.saveProfile();

      expect(userProfileServiceMock.updateProfile).toHaveBeenCalled();
    });

    it('should show success message on save', async () => {
      jest.useFakeTimers();

      await component.saveProfile();

      expect(component.showSuccess()).toBe(true);

      jest.advanceTimersByTime(2000);
      expect(component.showSuccess()).toBe(false);

      jest.useRealTimers();
    });

    it('should set isSaving during save', async () => {
      const savePromise = component.saveProfile();
      expect(component.isSaving()).toBe(true);

      await savePromise;
      expect(component.isSaving()).toBe(false);
    });

    it('should send correct data to service', async () => {
      const profile = component.profile();
      component.profile.set({
        ...profile,
        weight: 80,
        age: 30
      });

      await component.saveProfile();

      const expectedInput: UserProfileInput = expect.objectContaining({
        weight: 80,
        age: 30
      });

      expect(userProfileServiceMock.updateProfile).toHaveBeenCalledWith(expectedInput);
    });

    it('should set weekly_rate to 0 when goal_type is maintain', async () => {
      component.profile.set({
        ...component.profile(),
        goal_type: 'maintain',
        weekly_rate: -0.5
      });

      await component.saveProfile();

      const callArgs = (userProfileServiceMock.updateProfile as jest.Mock).mock.calls[0][0];
      expect(callArgs.weekly_rate).toBe(0);
    });

    it('should preserve weekly_rate when goal_type is not maintain', async () => {
      component.profile.set({
        ...component.profile(),
        goal_type: 'deficit',
        weekly_rate: -0.5
      });

      await component.saveProfile();

      const callArgs = (userProfileServiceMock.updateProfile as jest.Mock).mock.calls[0][0];
      expect(callArgs.weekly_rate).toBe(-0.5);
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      await component.ngOnInit();
    });

    it('should handle validation errors', async () => {
      const validationErrors = [
        { loc: ['body', 'weight'], msg: 'Invalid weight', type: 'value_error' },
        { loc: ['body', 'age'], msg: 'Invalid age', type: 'value_error' }
      ];

      (userProfileServiceMock.updateProfile as jest.Mock).mockRejectedValueOnce(
        validationErrors
      );

      await component.saveProfile();

      expect(component.validationErrors()).toEqual({
        weight: 'Invalid weight',
        age: 'Invalid age'
      });
    });

    it('should clear validation errors before save', async () => {
      component.validationErrors.set({ weight: 'Error' });

      await component.saveProfile();

      expect(component.validationErrors()).toEqual({});
    });

    it('should handle non-validation errors', async () => {
      (userProfileServiceMock.updateProfile as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      );

      await component.saveProfile();

      expect(component.isSaving()).toBe(false);
    });

    it('should reset isSaving even on error', async () => {
      (userProfileServiceMock.updateProfile as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      );

      await component.saveProfile();

      expect(component.isSaving()).toBe(false);
    });
  });

  describe('Profile Updates', () => {
    it('should allow multiple save operations', async () => {
      await component.ngOnInit();

      component.profile.update(p => ({ ...p, weight: 75 }));
      await component.saveProfile();

      component.profile.update(p => ({ ...p, weight: 70 }));
      await component.saveProfile();

      expect(userProfileServiceMock.updateProfile).toHaveBeenCalledTimes(2);
    });

    it('should maintain profile consistency', async () => {
      await component.ngOnInit();

      const email = component.profile().email;

      component.profile.update(p => ({ ...p, weight: 75 }));

      expect(component.profile().email).toBe(email);
    });
  });
});
