# Core Web Vitals & Performance Optimization Guide
<!-- Domain Zero Protocol v8.10.0 - Offline Reference -->

**Agent**: Maki (Performance Optimization Specialist)
**Last Updated**: 2025-12-26
**Sources**: [web.dev](https://web.dev/), [Google Core Web Vitals](https://developers.google.com/search/docs/appearance/core-web-vitals)

---

## Table of Contents

1. [Core Web Vitals Overview](#core-web-vitals-overview)
2. [Largest Contentful Paint (LCP)](#largest-contentful-paint-lcp)
3. [Interaction to Next Paint (INP)](#interaction-to-next-paint-inp)
4. [Cumulative Layout Shift (CLS)](#cumulative-layout-shift-cls)
5. [Measurement Tools](#measurement-tools)
6. [Performance Profiling](#performance-profiling)
7. [Bundle Optimization](#bundle-optimization)
8. [Caching Strategies](#caching-strategies)
9. [Quick Reference](#quick-reference)

---

## Core Web Vitals Overview

Core Web Vitals are Google's user-centric metrics for measuring web performance.

### The Three Metrics

| Metric | Measures | Good | Needs Improvement | Poor |
|--------|----------|------|-------------------|------|
| **LCP** | Loading | ≤ 2.5s | 2.5s - 4s | > 4s |
| **INP** | Interactivity | ≤ 200ms | 200ms - 500ms | > 500ms |
| **CLS** | Visual Stability | ≤ 0.1 | 0.1 - 0.25 | > 0.25 |

### Measurement Standards

- Measure at the **75th percentile**
- Include both **mobile and desktop** devices
- Use **field data** (real users) for assessment
- Use **lab data** (synthetic) for debugging

---

## Largest Contentful Paint (LCP)

**Definition**: Time until the largest content element is rendered in the viewport.

### What Elements Count as LCP?

- `<img>` elements
- `<image>` elements inside `<svg>`
- `<video>` elements (poster image)
- Elements with `background-image` (loaded via `url()`)
- Block-level elements containing text nodes

### LCP Optimization Strategies

#### 1. Optimize Critical Resources

```html
<!-- Preload LCP image -->
<link rel="preload" as="image" href="hero.webp" fetchpriority="high">

<!-- Preconnect to external domains -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.example.com" crossorigin>
```

#### 2. Optimize Images

```html
<!-- Use modern formats -->
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" alt="Hero" loading="eager" fetchpriority="high">
</picture>

<!-- Responsive images -->
<img srcset="hero-400.webp 400w,
             hero-800.webp 800w,
             hero-1200.webp 1200w"
     sizes="(max-width: 600px) 400px,
            (max-width: 1200px) 800px,
            1200px"
     src="hero-800.webp"
     alt="Hero image">
```

#### 3. Eliminate Render-Blocking Resources

```html
<!-- Defer non-critical CSS -->
<link rel="stylesheet" href="critical.css">
<link rel="preload" href="non-critical.css" as="style" onload="this.onload=null;this.rel='stylesheet'">

<!-- Defer JavaScript -->
<script src="app.js" defer></script>
<!-- Or async for independent scripts -->
<script src="analytics.js" async></script>
```

#### 4. Server-Side Optimization

```nginx
# Enable compression (nginx)
gzip on;
gzip_types text/html text/css application/javascript image/svg+xml;

# Enable caching
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

#### 5. Use CDN

- Serve static assets from edge locations
- Reduce Time to First Byte (TTFB)
- Enable HTTP/2 or HTTP/3

### LCP Debugging

```javascript
// Measure LCP with web-vitals library
import { onLCP } from 'web-vitals';

onLCP(({ value, entries }) => {
  console.log('LCP:', value);
  entries.forEach((entry) => {
    console.log('LCP Element:', entry.element);
    console.log('LCP URL:', entry.url);
  });
});
```

---

## Interaction to Next Paint (INP)

**Definition**: Time from user interaction to the next frame paint (replaces FID in 2024).

### What Interactions Count?

- Click/tap
- Keyboard input
- Touch/drag events

**Does NOT include**: Scroll, hover (without click)

### INP Optimization Strategies

#### 1. Break Up Long Tasks

```javascript
// BAD: Long synchronous task
function processLargeDataset(data) {
  for (const item of data) {
    processItem(item); // Blocks main thread
  }
}

// GOOD: Yield to main thread
async function processLargeDataset(data) {
  for (const item of data) {
    processItem(item);
    // Yield every 50ms
    if (performance.now() - start > 50) {
      await yieldToMain();
      start = performance.now();
    }
  }
}

function yieldToMain() {
  return new Promise((resolve) => {
    setTimeout(resolve, 0);
  });
}

// BETTER: Use scheduler API
async function processLargeDataset(data) {
  for (const item of data) {
    await scheduler.yield(); // Native yield
    processItem(item);
  }
}
```

#### 2. Optimize Event Handlers

```javascript
// BAD: Heavy computation in handler
button.addEventListener('click', () => {
  const result = heavyComputation(); // Blocks paint
  updateUI(result);
});

// GOOD: Defer non-visual work
button.addEventListener('click', () => {
  // Update UI immediately
  showLoadingState();

  // Defer heavy work
  requestIdleCallback(() => {
    const result = heavyComputation();
    updateUI(result);
  });
});
```

#### 3. Debounce Input Handlers

```javascript
function debounce(fn, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

// Debounce search input
const handleSearch = debounce((query) => {
  performSearch(query);
}, 300);

input.addEventListener('input', (e) => handleSearch(e.target.value));
```

#### 4. Use Web Workers for Heavy Computation

```javascript
// main.js
const worker = new Worker('worker.js');

button.addEventListener('click', () => {
  showLoadingState();
  worker.postMessage({ data: largeDataset });
});

worker.onmessage = (e) => {
  updateUI(e.data.result);
};

// worker.js
self.onmessage = (e) => {
  const result = heavyComputation(e.data);
  self.postMessage({ result });
};
```

### INP Debugging

```javascript
import { onINP } from 'web-vitals';

onINP(({ value, entries }) => {
  console.log('INP:', value);
  entries.forEach((entry) => {
    console.log('INP Event:', entry.name);
    console.log('Target:', entry.target);
    console.log('Processing Time:', entry.processingEnd - entry.processingStart);
  });
});
```

---

## Cumulative Layout Shift (CLS)

**Definition**: Sum of all unexpected layout shift scores during page lifetime.

### Layout Shift Score Formula

```
Layout Shift Score = Impact Fraction × Distance Fraction
```

- **Impact Fraction**: Viewport area affected by unstable elements
- **Distance Fraction**: Distance elements moved relative to viewport

### CLS Optimization Strategies

#### 1. Set Dimensions on Media

```html
<!-- Always set width and height -->
<img src="photo.jpg" width="800" height="600" alt="Photo">

<!-- Or use aspect-ratio -->
<style>
  .video-container {
    aspect-ratio: 16 / 9;
    width: 100%;
  }
</style>
```

#### 2. Reserve Space for Dynamic Content

```css
/* Reserve space for ads */
.ad-container {
  min-height: 250px;
}

/* Reserve space for async content */
.content-placeholder {
  min-height: 200px;
  background: #f0f0f0;
}
```

#### 3. Avoid Inserting Content Above Existing Content

```javascript
// BAD: Insert at top
container.prepend(newElement);

// GOOD: Insert at bottom or below viewport
container.append(newElement);

// OR notify user
if (isAboveViewport) {
  showNotification('New content available');
}
```

#### 4. Font Loading Strategy

```html
<!-- Preload critical fonts -->
<link rel="preload" href="font.woff2" as="font" type="font/woff2" crossorigin>

<style>
  /* Use font-display: optional to prevent FOIT/FOUT */
  @font-face {
    font-family: 'MyFont';
    src: url('font.woff2') format('woff2');
    font-display: optional;
  }

  /* Or use swap with size-adjust */
  @font-face {
    font-family: 'MyFont';
    src: url('font.woff2') format('woff2');
    font-display: swap;
    size-adjust: 100.5%; /* Match fallback metrics */
  }
</style>
```

#### 5. Use Transform for Animations

```css
/* BAD: Causes layout shift */
.element {
  animation: slide 0.3s;
}
@keyframes slide {
  from { margin-left: 0; }
  to { margin-left: 100px; }
}

/* GOOD: No layout shift */
.element {
  animation: slide 0.3s;
}
@keyframes slide {
  from { transform: translateX(0); }
  to { transform: translateX(100px); }
}
```

### CLS Debugging

```javascript
import { onCLS } from 'web-vitals';

onCLS(({ value, entries }) => {
  console.log('CLS:', value);
  entries.forEach((entry) => {
    entry.sources.forEach((source) => {
      console.log('Shifted Element:', source.node);
      console.log('Previous Rect:', source.previousRect);
      console.log('Current Rect:', source.currentRect);
    });
  });
});
```

---

## Measurement Tools

### Field Data (Real Users)

| Tool | Description |
|------|-------------|
| **Chrome User Experience Report (CrUX)** | Google's public dataset of real user metrics |
| **PageSpeed Insights** | CrUX data with Lighthouse analysis |
| **Search Console** | Core Web Vitals report for your site |
| **web-vitals library** | Measure CWV in your own analytics |

### Lab Data (Synthetic)

| Tool | Description |
|------|-------------|
| **Lighthouse** | Comprehensive performance audit |
| **Chrome DevTools** | Performance panel for detailed profiling |
| **WebPageTest** | Advanced testing with filmstrip view |

### Using web-vitals Library

```javascript
import { onLCP, onINP, onCLS } from 'web-vitals';

function sendToAnalytics({ name, value, id }) {
  // Send to your analytics
  gtag('event', name, {
    event_category: 'Web Vitals',
    event_label: id,
    value: Math.round(name === 'CLS' ? value * 1000 : value),
    non_interaction: true,
  });
}

onLCP(sendToAnalytics);
onINP(sendToAnalytics);
onCLS(sendToAnalytics);
```

---

## Performance Profiling

### Chrome DevTools Performance Panel

1. **Open DevTools** → Performance tab
2. **Start Recording** → Interact with page → Stop
3. **Analyze**:
   - Main thread activity
   - Long tasks (> 50ms)
   - Layout shifts
   - Network waterfall

### Key Metrics to Watch

```
TTFB (Time to First Byte) - Server response time
FCP (First Contentful Paint) - First content rendered
LCP (Largest Contentful Paint) - Main content rendered
TTI (Time to Interactive) - Page fully interactive
TBT (Total Blocking Time) - Time main thread blocked
CLS (Cumulative Layout Shift) - Visual stability
```

### Lighthouse Performance Audit

```bash
# CLI
npm install -g lighthouse
lighthouse https://example.com --view

# Node.js
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
const result = await lighthouse('https://example.com', {
  port: chrome.port,
  onlyCategories: ['performance'],
});
console.log('Performance Score:', result.lhr.categories.performance.score * 100);
await chrome.kill();
```

---

## Bundle Optimization

### Analyze Bundle Size

```bash
# webpack
npm install webpack-bundle-analyzer
npx webpack-bundle-analyzer stats.json

# Vite
npm install rollup-plugin-visualizer
# Add to vite.config.js

# Check package size
npx bundlephobia react-router-dom
```

### Code Splitting

```javascript
// React lazy loading
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <HeavyComponent />
    </Suspense>
  );
}

// Route-based splitting
const routes = [
  {
    path: '/dashboard',
    component: lazy(() => import('./Dashboard')),
  },
  {
    path: '/settings',
    component: lazy(() => import('./Settings')),
  },
];
```

### Tree Shaking

```javascript
// BAD: Import entire library
import _ from 'lodash';
_.debounce(fn, 300);

// GOOD: Import only what you need
import debounce from 'lodash/debounce';
debounce(fn, 300);

// OR use lodash-es for tree shaking
import { debounce } from 'lodash-es';
```

### Minimize Dependencies

```bash
# Find unused dependencies
npx depcheck

# Check for duplicates
npm dedupe

# Find lighter alternatives
# bundlephobia.com
```

---

## Caching Strategies

### HTTP Caching

```nginx
# Static assets (immutable)
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
}

# HTML (revalidate)
location ~* \.html$ {
    add_header Cache-Control "no-cache, must-revalidate";
}

# API responses (no cache)
location /api/ {
    add_header Cache-Control "no-store";
}
```

### Service Worker Caching

```javascript
// sw.js
const CACHE_NAME = 'v1';
const STATIC_ASSETS = [
  '/',
  '/styles.css',
  '/app.js',
  '/offline.html',
];

// Install: Cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

// Fetch: Cache-first for static, network-first for API
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    // Network first for API
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  } else {
    // Cache first for static
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});
```

---

## Quick Reference

### Performance Budget

| Resource Type | Budget |
|--------------|--------|
| Total JS | < 300KB (compressed) |
| Total CSS | < 100KB (compressed) |
| Total Images | < 1MB |
| Total Fonts | < 100KB |
| LCP | < 2.5s |
| INP | < 200ms |
| CLS | < 0.1 |

### Optimization Checklist

**LCP**
- [ ] Preload LCP image
- [ ] Use modern image formats (WebP, AVIF)
- [ ] Optimize server response time
- [ ] Remove render-blocking resources
- [ ] Use CDN

**INP**
- [ ] Break up long tasks (< 50ms)
- [ ] Use Web Workers for heavy computation
- [ ] Debounce input handlers
- [ ] Optimize third-party scripts

**CLS**
- [ ] Set dimensions on images/videos
- [ ] Reserve space for dynamic content
- [ ] Avoid inserting content above viewport
- [ ] Use font-display: optional

### Commands

```bash
# Lighthouse CLI
lighthouse https://example.com --output html --output-path report.html

# WebPageTest CLI
webpagetest test https://example.com -k API_KEY

# Check bundle size
npx source-map-explorer dist/*.js

# Performance budget check
npx bundlesize
```

---

**Online References**:
- [web.dev Performance](https://web.dev/performance/)
- [Google Core Web Vitals](https://developers.google.com/search/docs/appearance/core-web-vitals)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
