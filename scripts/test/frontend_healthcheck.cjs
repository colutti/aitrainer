const http = require('http');

// nosemgrep: problem-based-packs.insecure-transport.js-node.using-http-server.using-http-server
const request = http.get(
  {
    host: 'localhost',
    port: 3000,
    timeout: 5000,
    path: '/',
  },
  (res) => {
    process.exit(res.statusCode >= 200 && res.statusCode < 500 ? 0 : 1);
  }
);

request.on('error', () => {
  process.exit(1);
});

request.end();
