import { setupZoneTestEnv } from 'jest-preset-angular/setup-env/zone';

Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: () => {
    return {
      fillRect: () => {},
      clearRect: () => {},
      getImageData: (x: number, y: number, w: number, h: number) => {
        return {
          data: new Array(w * h * 4)
        };
      },
      putImageData: () => {},
      createImageData: () => { return []; },
      setTransform: () => {},
      drawImage: () => {},
      save: () => {},
      restore: () => {},
      beginPath: () => {},
      moveTo: () => {},
      lineTo: () => {},
      closePath: () => {},
      stroke: () => {},
      translate: () => {},
      scale: () => {},
      rotate: () => {},
      arc: () => {},
      fill: () => {},
      measureText: () => { return { width: 0 }; },
      transform: () => {},
      rect: () => {},
      clip: () => {},
    };
  }
});

setupZoneTestEnv();

// Mock TextDecoder/Encoder (needed for streaming)
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock Stream API (needed for streaming)
const { ReadableStream, TransformStream } = require('stream/web');
Object.assign(global, { ReadableStream, TransformStream });
