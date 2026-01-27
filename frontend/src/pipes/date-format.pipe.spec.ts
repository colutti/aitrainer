import { AppDateFormatPipe } from './date-format.pipe';

describe('AppDateFormatPipe', () => {
  let pipe: AppDateFormatPipe;

  beforeEach(() => {
    pipe = new AppDateFormatPipe();
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should be standalone', () => {
    // Pipe should be a standalone pipe
    expect(pipe instanceof AppDateFormatPipe).toBe(true);
  });

  it('should handle null value', () => {
    expect(pipe.transform(null)).toBeNull();
  });
});
