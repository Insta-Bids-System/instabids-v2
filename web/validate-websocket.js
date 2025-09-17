#!/usr/bin/env node

/**
 * Quick WebSocket validation script
 * Run this while testing to verify single WebSocket behavior
 */

const { execSync } = require('child_process');
const https = require('https');

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, message) {
  console.log(color + message + colors.reset);
}

function checkContainerConnections() {
  try {
    log(colors.blue, '🔍 Checking backend WebSocket connections...');
    
    // Check established connections to port 8008
    const result = execSync('ss -tan | grep ":8008 " | grep ESTAB | wc -l', { encoding: 'utf8' });
    const connectionCount = parseInt(result.trim());
    
    log(colors.yellow, `📊 Active connections to backend:8008: ${connectionCount}`);
    
    if (connectionCount <= 2) {
      log(colors.green, '✅ PASS: Connection count is low (likely shared WebSocket working)');
    } else {
      log(colors.red, `❌ FAIL: Too many connections (${connectionCount}). WebSocket stampede detected!`);
    }
    
    return connectionCount;
  } catch (error) {
    log(colors.red, '❌ Error checking connections: ' + error.message);
    return -1;
  }
}

function checkDockerContainers() {
  try {
    log(colors.blue, '🐳 Checking Docker containers...');
    
    const result = execSync('docker ps --format "{{.Names}}: {{.Status}}" | grep instabids', { encoding: 'utf8' });
    const containers = result.trim().split('\\n');
    
    containers.forEach(container => {
      if (container.includes('Up')) {
        log(colors.green, `✅ ${container}`);
      } else {
        log(colors.red, `❌ ${container}`);
      }
    });
    
  } catch (error) {
    log(colors.red, '❌ Error checking Docker containers: ' + error.message);
  }
}

async function testBackendAPI() {
  try {
    log(colors.blue, '🌐 Testing backend API...');
    
    const response = await fetch('http://localhost:8008/');
    const status = response.status;
    
    if (status === 200 || status === 401) { // 401 is OK (no session)
      log(colors.green, `✅ Backend API responding (${status})`);
    } else {
      log(colors.red, `❌ Backend API error: ${status}`);
    }
  } catch (error) {
    log(colors.red, '❌ Backend API not reachable: ' + error.message);
  }
}

function generateTestInstructions() {
  log(colors.blue, '\\n📋 MANUAL TEST INSTRUCTIONS:');
  log(colors.yellow, '\\n1. Open Window A and Window B');
  log(colors.yellow, '2. In each window, open 3 tabs to http://localhost:5173');
  log(colors.yellow, '3. Open DevTools → Network → WS in any tab');
  log(colors.yellow, '4. You should see only ONE 101 Switching Protocols handshake');
  log(colors.yellow, '\\n5. In browser console, run:');
  log(colors.blue, '   console.log(window.__WS_DEBUG__)');
  log(colors.yellow, '   Expected: { activeSocketCount: 1, ... }');
  log(colors.yellow, '\\n6. Close/open tabs quickly and re-run this script');
  log(colors.yellow, '   Connection count should stay ~1-2, not grow to 6+');
  
  log(colors.blue, '\\n🧪 CIRCUIT BREAKER TEST:');
  log(colors.yellow, 'In browser console:');
  log(colors.blue, 'fetch("/api/fake-endpoint").catch(console.log); // Repeat 5x');
  log(colors.yellow, 'After 3 failures, should see "Circuit is OPEN" messages');
}

async function main() {
  log(colors.green, '🚀 WebSocket Validation Script');
  log(colors.green, '===============================\\n');
  
  // Check Docker containers
  checkDockerContainers();
  
  // Check backend API
  await testBackendAPI();
  
  // Check connections
  const connections = checkContainerConnections();
  
  // Generate test instructions
  generateTestInstructions();
  
  // Summary
  log(colors.blue, '\\n📊 SUMMARY:');
  if (connections <= 2) {
    log(colors.green, '✅ System appears to be using shared WebSocket correctly');
  } else {
    log(colors.red, '❌ WebSocket stampede detected - check SharedWorker configuration');
  }
  
  log(colors.yellow, '\\nRun this script periodically while testing to monitor connection count.');
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  log(colors.yellow, '\\n👋 Validation script stopped');
  process.exit(0);
});

main().catch(console.error);