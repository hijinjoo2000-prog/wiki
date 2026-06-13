const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 18080;
const server = http.createServer((req, res) => {
    const filePath = path.join(__dirname, 'test.html');
    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end('Error loading test.html: ' + err.message);
        } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(data);
        }
    });
});

server.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
});
