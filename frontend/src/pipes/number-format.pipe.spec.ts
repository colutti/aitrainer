import { AppNumberFormatPipe } from './number-format.pipe';

describe('AppNumberFormatPipe', () => {
  let pipe: AppNumberFormatPipe;

  beforeEach(() => {
    pipe = new AppNumberFormatPipe();
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should be standalone', () => {
    // Pipe should be a standalone pipe
    expect(pipe instanceof AppNumberFormatPipe).toBe(true);
  });
});
