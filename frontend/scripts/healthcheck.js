const http = require('http');

const options = {
  host: 'localhost',
  port: 3000,
  timeout: 5000,
  path: '/'
};

const request = http.get(options, (res) => {
  console.log(`STATUS: ${res.statusCode}`);
  if (res.statusCode >= 200 && res.statusCode < 400) {
    process.exit(0);
  } else {
    process.exit(1);
  }
});

request.on('error', (err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});

request.end();
