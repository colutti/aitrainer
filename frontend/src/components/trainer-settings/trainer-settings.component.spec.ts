import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TrainerSettingsComponent } from './trainer-settings.component';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { NotificationService } from '../../services/notification.service';
import { signal } from '@angular/core';
import { TrainerFactory } from '../../test-utils/factories/trainer.factory';
import { TrainerCard, TrainerProfile } from '../../models/trainer-profile.model';

describe('TrainerSettingsComponent', () => {
  let component: TrainerSettingsComponent;
  let fixture: ComponentFixture<TrainerSettingsComponent>;
  let trainerServiceMock: Partial<TrainerProfileService>;
  let notificationServiceMock: Partial<NotificationService>;

  const mockTrainers: TrainerCard[] = [
    { trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png' },
    { trainer_id: 'luna', name: 'Luna', avatar_url: '/assets/luna.png' }
  ];

  const mockProfile: TrainerProfile = {
    trainer_type: 'atlas'
  };

  beforeEach(async () => {
    trainerServiceMock = {
      getAvailableTrainers: jest.fn().mockResolvedValue(mockTrainers),
      fetchProfile: jest.fn().mockResolvedValue(mockProfile),
      updateProfile: jest.fn().mockResolvedValue({ trainer_type: 'luna' })
    };

    notificationServiceMock = {
      success: jest.fn(),
      error: jest.fn()
    };

    await TestBed.configureTestingModule({
      imports: [TrainerSettingsComponent],
      providers: [
        { provide: TrainerProfileService, useValue: trainerServiceMock },
        { provide: NotificationService, useValue: notificationServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TrainerSettingsComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should load trainers on init', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(trainerServiceMock.getAvailableTrainers).toHaveBeenCalled();
      expect(component.availableTrainers().length).toBe(2);
    });

    it('should load current profile on init', async () => {
      await component.ngOnInit();
      fixture.detectChanges();
      await fixture.whenStable();

      expect(trainerServiceMock.fetchProfile).toHaveBeenCalled();
      expect(component.profile().trainer_type).toBe('atlas');
    });

    it('should handle error loading trainers', async () => {
      (trainerServiceMock.getAvailableTrainers as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      expect(notificationServiceMock.error).toHaveBeenCalledWith(
        'Erro ao carregar treinadores disponíveis.'
      );
    });

    it('should initialize with default profile', () => {
      expect(component.profile()).toBeDefined();
      expect(component.isSaving()).toBe(false);
    });
  });

  describe('Trainer Selection', () => {
    it('should update selected trainer locally', () => {
      component.selectTrainer('luna');

      expect(component.profile().trainer_type).toBe('luna');
    });

    it('should not save automatically when selecting trainer', () => {
      component.selectTrainer('luna');

      expect(trainerServiceMock.updateProfile).not.toHaveBeenCalled();
    });

    it('should allow switching between trainers', () => {
      component.selectTrainer('luna');
      expect(component.profile().trainer_type).toBe('luna');

      component.selectTrainer('atlas');
      expect(component.profile().trainer_type).toBe('atlas');
    });
  });

  describe('Save Profile', () => {
    beforeEach(async () => {
      fixture.detectChanges();
      await fixture.whenStable();
    });

    it('should save profile successfully', async () => {
      component.selectTrainer('luna');
      await component.saveProfile();

      expect(trainerServiceMock.updateProfile).toHaveBeenCalledWith({ trainer_type: 'luna' });
      expect(notificationServiceMock.success).toHaveBeenCalledWith(
        'Treinador atualizado com sucesso!'
      );
    });

    it('should set isSaving signal during save', async () => {
      component.selectTrainer('luna');

      const savePromise = component.saveProfile();
      expect(component.isSaving()).toBe(true);

      await savePromise;
      expect(component.isSaving()).toBe(false);
    });

    it('should update profile with response from API', async () => {
      component.selectTrainer('luna');
      await component.saveProfile();

      expect(component.profile().trainer_type).toBe('luna');
    });

    it('should handle save error', async () => {
      (trainerServiceMock.updateProfile as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      );

      component.selectTrainer('luna');
      await component.saveProfile();

      expect(notificationServiceMock.error).toHaveBeenCalledWith(
        'Erro ao salvar alterações. Tente novamente.'
      );
      expect(component.isSaving()).toBe(false);
    });

    it('should reset isSaving even on error', async () => {
      (trainerServiceMock.updateProfile as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      );

      component.selectTrainer('luna');
      await component.saveProfile();

      expect(component.isSaving()).toBe(false);
    });
  });

  describe('Profile Loading', () => {
    it('should handle profile load error gracefully', async () => {
      (trainerServiceMock.fetchProfile as jest.Mock).mockRejectedValueOnce(
        new Error('API Error')
      );

      // Should not throw
      await component.loadProfile();

      expect(component.profile()).toBeDefined();
    });

    it('should update profile when fetched', async () => {
      const newProfile: TrainerProfile = { trainer_type: 'luna' };
      (trainerServiceMock.fetchProfile as jest.Mock).mockResolvedValueOnce(newProfile);

      await component.loadProfile();

      expect(component.profile().trainer_type).toBe('luna');
    });
  });

  describe('Component State', () => {
    it('should maintain availability of trainers list', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.availableTrainers()).toEqual(mockTrainers);
    });

    it('should allow multiple save operations', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      component.selectTrainer('luna');
      await component.saveProfile();

      component.selectTrainer('atlas');
      await component.saveProfile();

      expect(trainerServiceMock.updateProfile).toHaveBeenCalledTimes(2);
    });
  });
});
