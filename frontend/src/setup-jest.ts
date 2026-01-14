import 'jest-preset-angular/setup-env/zone';


// Mock TextDecoder/Encoder (needed for streaming)
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock Stream API (needed for streaming)
const { ReadableStream, TransformStream } = require('stream/web');
Object.assign(global, { ReadableStream, TransformStream });
