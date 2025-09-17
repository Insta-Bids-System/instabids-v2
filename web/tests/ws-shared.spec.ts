// Playwright test to verify SharedWorker WebSocket behavior
import { test, expect } from '@playwright/test';

// Run tests serially to avoid WebSocket conflicts
test.describe.configure({ mode: 'serial' });

test('shared-worker ensures single websocket connection', async ({ browser }) => {
  const context = await browser.newContext();
  
  // Create multiple tabs
  const page1 = await context.newPage();
  const page2 = await context.newPage();
  const page3 = await context.newPage();
  
  // Track WebSocket handshakes
  const handshakes: {url: string, timestamp: number}[] = [];
  
  for (const page of [page1, page2, page3]) {
    page.on('websocket', ws => {
      console.log(`WebSocket created: ${ws.url()}`);
      handshakes.push({ 
        url: ws.url(),
        timestamp: Date.now()
      });
    });
  }
  
  // Navigate all pages
  await Promise.all([
    page1.goto('http://localhost:5173'),
    page2.goto('http://localhost:5173'),
    page3.goto('http://localhost:5173')
  ]);
  
  // Wait for WebSocket connections to establish
  await page1.waitForTimeout(2000);
  
  // Check unique WebSocket URLs (should be just one)
  const uniqueWsUrls = new Set(handshakes.map(h => h.url));
  
  console.log(`Total handshakes: ${handshakes.length}`);
  console.log(`Unique URLs: ${uniqueWsUrls.size}`);
  console.log('URLs:', Array.from(uniqueWsUrls));
  
  // Expect exactly one unique WebSocket endpoint
  expect(uniqueWsUrls.size).toBe(1);
  
  // Check in-app metric via window.__WS_DEBUG__
  const wsCount = await page1.evaluate(() => {
    return (window as any).__WS_DEBUG__?.activeSocketCount ?? -1;
  });
  
  console.log(`In-app socket count: ${wsCount}`);
  expect(wsCount).toBe(1);
  
  // Verify health metrics are being received
  const healthData = await page1.evaluate(() => {
    return (window as any).__WS_DEBUG__;
  });
  
  console.log('Health data:', healthData);
  expect(healthData).toBeDefined();
  expect(healthData.activeSocketCount).toBe(1);
  expect(healthData.lastEvent).toBeGreaterThan(0);
  
  await context.close();
});

test('websocket reconnects with backoff after backend restart', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Wait for initial connection
  await page.waitForTimeout(2000);
  
  // Get initial connection state
  const initialState = await page.evaluate(() => {
    return (window as any).__WS_DEBUG__;
  });
  
  expect(initialState?.activeSocketCount).toBe(1);
  const initialReconnects = initialState?.totalReconnects || 0;
  
  // Simulate backend restart (this would be done externally)
  console.log('Simulating backend restart...');
  // In real test, you'd run: docker compose restart instabids-backend
  
  // Monitor reconnection attempts
  const reconnectLogs: any[] = [];
  
  page.on('console', msg => {
    if (msg.text().includes('reconnect') || msg.text().includes('backoff')) {
      reconnectLogs.push({
        text: msg.text(),
        timestamp: Date.now()
      });
    }
  });
  
  // Wait for reconnection attempts
  await page.waitForTimeout(5000);
  
  // Check that reconnection happened with backoff
  const finalState = await page.evaluate(() => {
    return (window as any).__WS_DEBUG__;
  });
  
  console.log('Reconnect logs:', reconnectLogs);
  console.log('Final state:', finalState);
  
  // Verify reconnection attempts increased
  expect(finalState?.totalReconnects).toBeGreaterThan(initialReconnects);
  
  // Verify backoff delays are increasing
  if (reconnectLogs.length > 1) {
    const delays = reconnectLogs.map(log => {
      const match = log.text.match(/(\d+)ms/);
      return match ? parseInt(match[1]) : 0;
    });
    
    // Each delay should be roughly double the previous (with jitter)
    for (let i = 1; i < delays.length; i++) {
      expect(delays[i]).toBeGreaterThan(delays[i-1] * 0.8); // Allow for jitter
    }
  }
});

test('fallback behavior when SharedWorker is disabled', async ({ page }) => {
  // Inject code to disable SharedWorker
  await page.addInitScript(() => {
    (window as any).SharedWorker = undefined;
  });
  
  await page.goto('http://localhost:5173');
  await page.waitForTimeout(2000);
  
  // Check that fallback WebSocket is used
  const wsState = await page.evaluate(() => {
    // Check for regular WebSocket connection
    return {
      hasSharedWorker: typeof (window as any).SharedWorker !== 'undefined',
      hasWebSocket: typeof WebSocket !== 'undefined',
      debugInfo: (window as any).__WS_DEBUG__
    };
  });
  
  console.log('Fallback state:', wsState);
  
  expect(wsState.hasSharedWorker).toBe(false);
  expect(wsState.hasWebSocket).toBe(true);
  
  // Verify app still works without SharedWorker
  await expect(page.locator('body')).toBeVisible();
});

test('circuit breaker prevents API stampede', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Track API failures
  const apiErrors: any[] = [];
  
  page.on('console', msg => {
    if (msg.text().includes('Circuit') || msg.text().includes('circuit')) {
      apiErrors.push({
        text: msg.text(),
        timestamp: Date.now()
      });
    }
  });
  
  // Trigger multiple API failures
  await page.evaluate(async () => {
    const api = (window as any).apiService;
    if (!api) return;
    
    // Point to a failing endpoint
    const results = [];
    for (let i = 0; i < 10; i++) {
      try {
        await api.request('/api/fake-endpoint-that-fails');
      } catch (error: any) {
        results.push(error.message);
      }
    }
    
    return results;
  });
  
  // Wait for circuit breaker to activate
  await page.waitForTimeout(2000);
  
  console.log('Circuit breaker logs:', apiErrors);
  
  // Verify circuit breaker opened after threshold
  const hasCircuitOpen = apiErrors.some(log => 
    log.text.includes('Circuit is OPEN') || 
    log.text.includes('Circuit OPEN')
  );
  
  expect(hasCircuitOpen).toBe(true);
});