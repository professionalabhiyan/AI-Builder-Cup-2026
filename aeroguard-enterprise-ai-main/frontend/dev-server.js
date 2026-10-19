#!/usr/bin/env node
/**
 * FactoryMind Frontend Live Server (Port 4200)
 * Serves the real-time FactoryMind application on http://localhost:4200 (including /login and SPA routes).
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 4200;
const HTML_FILE = path.join(__dirname, '..', 'aeroguard_factorymind_dashboard.html');
const FALLBACK_HTML = path.join(__dirname, 'src', 'assets_portal.html');

const server = http.createServer((req, res) => {
  let targetPath = fs.existsSync(HTML_FILE) ? HTML_FILE : FALLBACK_HTML;
  fs.readFile(targetPath, 'utf8', (err, content) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error loading FactoryMind UI: ' + err.message);
      return;
    }
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache'
    });
    res.end(content);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log('\n==================================================================');
  console.log('  FactoryMind (AeroGuard AI v3.0) Frontend Live Server Running!');
  console.log('  -> Local URL:   http://localhost:' + PORT + '/');
  console.log('  -> Status:      Real-Time Telemetry, Per-Machine ROI & Live ML ON');
  console.log('==================================================================\n');
});
