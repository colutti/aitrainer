import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { StatsService } from '../../services/stats.service';
import { of } from 'rxjs';
import { signal } from '@angular/core';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { MetabolismService } from '../../services/metabolism.service';
import { NutritionService } from '../../services/nutrition.service';
import { WeightService } from '../../services/weight.service';

import { WorkoutStats } from '../../models/stats.model';
import { MetabolismResponse } from '../../models/metabolism.model';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let statsServiceMock: Partial<StatsService>;
  let nutritionServiceMock: Partial<NutritionService>;
  let metabolismServiceMock: Partial<MetabolismService>;
  let weightServiceMock: Partial<WeightService>;

  beforeEach(async () => {
    statsServiceMock = {
      fetchStats: jest.fn(),
      stats: signal(null),
      isLoading: signal(false)
    };

    nutritionServiceMock = {
      getStats: jest.fn().mockReturnValue(of(null)),
      stats: signal(null)
    };

    metabolismServiceMock = {
      getSummary: jest.fn().mockResolvedValue(null),
      stats: signal(null)
    };

    weightServiceMock = {
      getBodyCompositionStats: jest.fn().mockResolvedValue(null)
    };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: StatsService, useValue: statsServiceMock },
        { provide: NutritionService, useValue: nutritionServiceMock },
        { provide: MetabolismService, useValue: metabolismServiceMock },
        { provide: WeightService, useValue: weightServiceMock },
        provideCharts(withDefaultRegisterables())
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should fetch stats on init', () => {
    expect(statsServiceMock.fetchStats).toHaveBeenCalled();
  });

  it('should update chart when stats change', () => {
    const mockStats: WorkoutStats = {
      weekly_volume: [
        { category: 'Chest', volume: 1000 },
        { category: 'Legs', volume: 2000 }
      ],
      current_streak_weeks: 5,
      weekly_frequency: [true, false, true, false, true, false, false],
      last_workout: { id: '123', workout_type: 'Push', date: new Date().toISOString(), duration_minutes: 60 },
      recent_prs: []
    };
    
    // Trigger signal update using a setter or directly if it was a writable signal (it is readonly in component but derived from service)
    // The component "stats" property is: stats = this.statsService.stats;
    // So updating the service signal should trigger component effect.
    
    statsServiceMock.stats.set(mockStats);
    
    // Also set metabolism stats so widgets don't crash
    const mockMetabolism: MetabolismResponse = {
      latest_weight: 75,
      target_weight: 70,
      start_weight: 80,
      goal_type: 'lose',
      weeks_to_goal: 10,
      fat_change_kg: -2,
      muscle_change_kg: 1,
      end_fat_pct: 20,
      end_muscle_pct: 40,
      weight_trend: [],
      consistency: []
    };
    component.metabolismStats.set(mockMetabolism);

    fixture.detectChanges(); // Run change detection

    // Check if chart data was updated
    expect(component.barChartData.labels).toEqual(['Chest', 'Legs']);
    expect(component.barChartData.datasets[0].data).toEqual([1000, 2000]);
  });
});
