import { test, expect } from '@playwright/test';

/**
 * Counter Demo - Visual E2E Test
 * 
 * Domain Zero Protocol Integration:
 * - Tier 1 (Rapid): Optional demo for local development
 * - Tier 2 (Standard): Template for smoke tests
 * - Tier 3 (Critical): Foundation for comprehensive E2E coverage
 * 
 * Agent Mapping:
 * - Yuuji (Implementation): Creates/updates this spec
 * - Megumi (Security): Reviews test coverage for user flows
 * - Gojo (Mission Control): Monitors CI integration
 */

test.describe('Counter Demo', () => {
  test('should increment counter on button click', async ({ page }) => {
    // Create a simple HTML page with a counter
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Counter Demo</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100vh;
              margin: 0;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white;
            }
            h1 {
              margin-bottom: 2rem;
            }
            #counter {
              font-size: 4rem;
              margin: 2rem 0;
              font-weight: bold;
            }
            button {
              font-size: 1.5rem;
              padding: 1rem 2rem;
              background: white;
              color: #667eea;
              border: none;
              border-radius: 8px;
              cursor: pointer;
              box-shadow: 0 4px 6px rgba(0,0,0,0.2);
              transition: transform 0.1s;
            }
            button:hover {
              transform: scale(1.05);
            }
            button:active {
              transform: scale(0.95);
            }
          </style>
        </head>
        <body>
          <h1>Domain Zero - Counter Demo</h1>
          <div id="counter">0</div>
          <button id="increment">Increment</button>
          <script>
            let count = 0;
            const counterEl = document.getElementById('counter');
            const btn = document.getElementById('increment');
            
            btn.addEventListener('click', () => {
              count++;
              counterEl.textContent = count;
            });
          </script>
        </body>
      </html>
    `);

    // Verify initial state
    await expect(page.locator('#counter')).toHaveText('0');
    
    // Click increment button 3 times
    const incrementButton = page.locator('#increment');
    
    await incrementButton.click();
    await expect(page.locator('#counter')).toHaveText('1');
    
    await incrementButton.click();
    await expect(page.locator('#counter')).toHaveText('2');
    
    await incrementButton.click();
    await expect(page.locator('#counter')).toHaveText('3');
    
    // Verify final state
    await expect(page.locator('#counter')).toHaveText('3');
  });

  test('should have correct page title', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head><title>Counter Demo</title></head>
        <body><h1>Test</h1></body>
      </html>
    `);
    
    await expect(page).toHaveTitle('Counter Demo');
  });
});
