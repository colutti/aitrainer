import { BodyCompositionComponent } from './body-composition.component';

describe('BodyCompositionComponent', () => {
  it('should create', () => {
    expect(BodyCompositionComponent).toBeDefined();
  });

  it('should be a component', () => {
    const metadata = (BodyCompositionComponent as any).ɵcmp;
    expect(metadata).toBeDefined();
  });

  it('should be standalone', () => {
    const metadata = (BodyCompositionComponent as any).ɵcmp;
    expect(metadata.standalone).toBe(true);
  });

  it('should have selector', () => {
    const metadata = (BodyCompositionComponent as any).ɵcmp;
    expect(metadata.selectors).toBeDefined();
  });
});
