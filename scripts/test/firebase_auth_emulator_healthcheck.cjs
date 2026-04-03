const http = require('node:http');

const options = {
  host: '127.0.0.1',
  port: 9099,
  path: '/emulator/v1/projects/demo-fityq/oobCodes',
  method: 'GET',
  timeout: 3000,
};

const request = http.request(options, (response) => {
  if (response.statusCode >= 200 && response.statusCode < 500) {
    process.exit(0);
  }

  process.exit(1);
});

request.on('error', () => {
  process.exit(1);
});

request.on('timeout', () => {
  request.destroy();
  process.exit(1);
});

request.end();
