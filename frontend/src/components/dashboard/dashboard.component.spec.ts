import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { StatsService } from '../../services/stats.service';
import { of } from 'rxjs';
import { signal } from '@angular/core';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let statsServiceMock: any;

  beforeEach(async () => {
    statsServiceMock = {
      fetchStats: jest.fn(),
      stats: signal(null),
      isLoading: signal(false)
    };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: StatsService, useValue: statsServiceMock },
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
    const mockStats: any = {
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
    fixture.detectChanges(); // Run change detection

    // Check if chart data was updated
    expect(component.barChartData.labels).toEqual(['Chest', 'Legs']);
    expect(component.barChartData.datasets[0].data).toEqual([1000, 2000]);
  });
});
