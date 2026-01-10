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
