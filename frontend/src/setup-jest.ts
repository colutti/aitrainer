import 'jest-preset-angular/setup-env/zone';
import 'jest-canvas-mock';
import 'jest-canvas-mock';

global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

import { TestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting,
} from '@angular/platform-browser-dynamic/testing';
import { registerLocaleData } from '@angular/common';
import ptBr from '@angular/common/locales/pt';

// Register Portuguese (Brazil) locale data for pipes
registerLocaleData(ptBr);

TestBed.initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting(),
);

import { TextEncoder, TextDecoder } from 'util';
import { ReadableStream, TransformStream } from 'stream/web';

// Mock TextDecoder/Encoder (needed for streaming)
global.TextEncoder = TextEncoder as unknown as typeof global.TextEncoder;
global.TextDecoder = TextDecoder as unknown as typeof global.TextDecoder;

// Mock Stream API (needed for streaming)
Object.assign(global, { ReadableStream, TransformStream });
