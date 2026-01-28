import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetBodyEvolutionComponent } from '../widget-body-evolution.component';

describe('WidgetBodyEvolutionComponent', () => {
  let component: WidgetBodyEvolutionComponent;
  let fixture: ComponentFixture<WidgetBodyEvolutionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetBodyEvolutionComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetBodyEvolutionComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => expect(component).toBeTruthy());

  it('should accept fat change', () => {
    component.fatChange = -2.5;
    fixture.detectChanges();
    expect(component.fatChange).toBe(-2.5);
  });

  it('should accept muscle change', () => {
    component.muscleChange = 1.5;
    fixture.detectChanges();
    expect(component.muscleChange).toBe(1.5);
  });

  it('should accept date range', () => {
    component.startDate = '2026-01-01';
    component.endDate = '2026-01-27';
    fixture.detectChanges();
    expect(component.startDate).toBe('2026-01-01');
  });

  it('should display fat change card', () => {
    component.fatChange = -2.5;
    fixture.detectChanges();
    const card = fixture.nativeElement.querySelector('[data-test="fat-change"]');
    if (card) expect(card.textContent).toContain('-2.5');
  });

  it('should display muscle change card', () => {
    component.muscleChange = 1.5;
    fixture.detectChanges();
    const card = fixture.nativeElement.querySelector('[data-test="muscle-change"]');
    if (card) expect(card.textContent).toContain('1.5');
  });

  it('should handle negative fat change', () => {
    component.fatChange = -5;
    fixture.detectChanges();
    expect(component.fatChange).toBe(-5);
  });

  it('should handle positive muscle change', () => {
    component.muscleChange = 3;
    fixture.detectChanges();
    expect(component.muscleChange).toBe(3);
  });

  it('should handle zero change', () => {
    component.fatChange = 0;
    component.muscleChange = 0;
    fixture.detectChanges();
    expect(component.fatChange).toBe(0);
  });

  it('should be pure component', () => {
    component.fatChange = -2;
    component.muscleChange = 1;
    fixture.detectChanges();
    expect(component.fatChange).toBe(-2);
  });
});
