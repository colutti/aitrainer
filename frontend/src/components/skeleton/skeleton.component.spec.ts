import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SkeletonComponent } from './skeleton.component';

describe('SkeletonComponent', () => {
  let component: SkeletonComponent;
  let fixture: ComponentFixture<SkeletonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SkeletonComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(SkeletonComponent);
    component = fixture.componentInstance;
  });

  describe('Component Creation', () => {
    it('should create component', () => {
      expect(component).toBeTruthy();
    });

    it('should be standalone', () => {
      const metadata = (SkeletonComponent as any).ɵcmp;
      expect(metadata.standalone).toBe(true);
    });
  });

  describe('Default Input Values', () => {
    it('should have default width of 100%', () => {
      expect(component.width).toBe('100%');
    });

    it('should have default height of 1rem', () => {
      expect(component.height).toBe('1rem');
    });

    it('should have default shape of rect', () => {
      expect(component.shape).toBe('rect');
    });
  });

  describe('Width Input', () => {
    it('should accept and store width input', () => {
      component.width = '200px';
      expect(component.width).toBe('200px');
    });

    it('should accept percentage width', () => {
      component.width = '50%';
      expect(component.width).toBe('50%');
    });

    it('should handle rem units', () => {
      component.width = '15rem';
      expect(component.width).toBe('15rem');
    });

    it('should handle em units', () => {
      component.width = '10em';
      expect(component.width).toBe('10em');
    });

    it('should apply width style to element', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '250px';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('250px');
    });
  });

  describe('Height Input', () => {
    it('should accept and store height input', () => {
      component.height = '2rem';
      expect(component.height).toBe('2rem');
    });

    it('should accept pixel height', () => {
      component.height = '50px';
      expect(component.height).toBe('50px');
    });

    it('should apply height style to element', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.height = '80px';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.height).toBe('80px');
    });

    it('should handle various height units', () => {
      const heights = ['1rem', '50px', '2vh', '5em'];
      heights.forEach(h => {
        component.height = h;
        expect(component.height).toBe(h);
      });
    });
  });

  describe('Shape Input - Rect (Default)', () => {
    it('should have default rect shape', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-md')).toBe(true);
    });

    it('should apply rounded-md class for rect shape', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-md')).toBe(true);
    });

    it('should not have circle class when rect', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-full')).toBe(false);
    });
  });

  describe('Shape Input - Circle', () => {
    it('should apply rounded-full class for circle shape', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'circle';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-full')).toBe(true);
    });

    it('should not have rect class when circle', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'circle';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-md')).toBe(false);
    });
  });

  describe('Animation & Loading State', () => {
    it('should have animate-pulse class', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
    });

    it('should have background color class', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('bg-gray-700/50')).toBe(true);
    });

    it('should have rounded class', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded')).toBe(true);
    });

    it('should maintain animation on rect shape', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
    });

    it('should maintain animation on circle shape', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'circle';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
    });
  });

  describe('Combined Properties', () => {
    it('should apply width and height together', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '150px';
      component.height = '75px';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('150px');
      expect(skeleton.style.height).toBe('75px');
    });

    it('should apply rect shape with dimensions', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '100%';
      component.height = '2rem';
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('100%');
      expect(skeleton.style.height).toBe('2rem');
      expect(skeleton.classList.contains('rounded-md')).toBe(true);
    });

    it('should apply circle shape with dimensions', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '40px';
      component.height = '40px';
      component.shape = 'circle';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('40px');
      expect(skeleton.style.height).toBe('40px');
      expect(skeleton.classList.contains('rounded-full')).toBe(true);
    });

    it('should maintain all classes with various inputs', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '300px';
      component.height = '100px';
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
      expect(skeleton.classList.contains('bg-gray-700/50')).toBe(true);
      expect(skeleton.classList.contains('rounded')).toBe(true);
      expect(skeleton.classList.contains('rounded-md')).toBe(true);
    });
  });

  describe('Template Structure', () => {
    it('should render single div element', () => {
      fixture.detectChanges();
      const divs = fixture.nativeElement.querySelectorAll('div');
      expect(divs.length).toBe(1);
    });

    it('should have correct HTML structure', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.tagName.toLowerCase()).toBe('div');
    });

    it('should bind style properties correctly', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '200px';
      component.height = '100px';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.getAttribute('style')).toContain('width');
      expect(skeleton.getAttribute('style')).toContain('height');
    });
  });

  describe('Loading Placeholder Scenarios', () => {
    it('should work as text line skeleton', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '100%';
      component.height = '0.75rem';
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton).toBeTruthy();
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
    });

    it('should work as avatar skeleton (circle)', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '40px';
      component.height = '40px';
      component.shape = 'circle';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('40px');
      expect(skeleton.style.height).toBe('40px');
      expect(skeleton.classList.contains('rounded-full')).toBe(true);
    });

    it('should work as button skeleton', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '100px';
      component.height = '40px';
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('100px');
      expect(skeleton.style.height).toBe('40px');
      expect(skeleton.classList.contains('rounded-md')).toBe(true);
    });

    it('should work as card skeleton', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '100%';
      component.height = '200px';
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('100%');
      expect(skeleton.style.height).toBe('200px');
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very small dimensions', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '1px';
      component.height = '1px';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('1px');
      expect(skeleton.style.height).toBe('1px');
    });

    it('should handle very large dimensions', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '100%';
      component.height = '1000px';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('100%');
      expect(skeleton.style.height).toBe('1000px');
    });

    it('should handle viewport units', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = '100vw';
      component.height = '100vh';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toBe('100vw');
      expect(skeleton.style.height).toBe('100vh');
    });

    it('should handle calc expressions', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.width = 'calc(100% - 10px)';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.style.width).toContain('calc');
    });
  });

  describe('Inputs are Reactive', () => {
    it('should accept Input decorator for width', () => {
      const initialWidth = component.width;
      component.width = 'new-width';
      expect(component.width).not.toBe(initialWidth);
      expect(component.width).toBe('new-width');
    });

    it('should accept Input decorator for height', () => {
      const initialHeight = component.height;
      component.height = 'new-height';
      expect(component.height).not.toBe(initialHeight);
      expect(component.height).toBe('new-height');
    });

    it('should accept Input decorator for shape', () => {
      expect(component.shape).toBe('rect');
      component.shape = 'circle';
      expect(component.shape).toBe('circle');
    });
  });

  describe('Loading State Visibility', () => {
    it('should display skeleton when loading', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton).toBeTruthy();
      expect(skeleton.style.width).toBeTruthy();
    });

    it('should be visible with default dimensions', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('bg-gray-700/50')).toBe(true);
    });

    it('should show pulsing animation', () => {
      fixture.detectChanges();
      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('animate-pulse')).toBe(true);
    });
  });

  describe('Shape Variants', () => {
    it('should only support rect and circle shapes', () => {
      component.shape = 'rect';
      expect(component.shape).toBe('rect');

      component.shape = 'circle';
      expect(component.shape).toBe('circle');
    });

    it('should render correctly with shape rect', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'rect';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-md')).toBe(true);
    });

    it('should render correctly with shape circle', () => {
      fixture.destroy();
      fixture = TestBed.createComponent(SkeletonComponent);
      component = fixture.componentInstance;
      component.shape = 'circle';
      fixture.detectChanges();

      const skeleton = fixture.nativeElement.querySelector('div');
      expect(skeleton.classList.contains('rounded-full')).toBe(true);
    });
  });
});
